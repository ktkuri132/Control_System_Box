"""
主窗口 (统一架构版本)
串口和仿真模式共用相同的核心组件
唯一区别是数据接收方式不同
"""
import numpy as np
from collections import deque
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStatusBar, QMessageBox, QFileDialog,
    QStackedWidget, QButtonGroup, QRadioButton,
    QFrame, QLabel
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction

from ui.plot_widgets import MultiPlotWidget
from ui.unified_control_panel import UnifiedControlPanel
from ui.simulator_plot_widgets import SimulatorPlotWidget
from core.serial_manager import SerialManager
from core.data_buffer import DataManager
from core.performance_analyzer import PerformanceAnalyzer
from core.simulator_receiver import SimulatorReceiver
from core.unified_data_protocol import UnifiedData, HandshakeInfo, StateValue
from core.updater import AutoUpdater, get_current_version


class DataSourceMode:
    """数据源模式"""
    SERIAL = 0      # 串口模式
    SIMULATOR = 1   # 仿真数据模式


class MainWindow(QMainWindow):
    """主窗口 - 统一架构"""

    def __init__(self):
        super().__init__()
        
        # 当前模式
        self._current_mode = DataSourceMode.SERIAL
        
        # 初始化核心组件
        self._serial_manager = SerialManager()
        self._simulator_receiver = SimulatorReceiver()
        self._analyzer = PerformanceAnalyzer()
        
        # ★ 统一数据缓冲区 - 两种模式共用
        self._data_buffer = {
            'timestamps': deque(maxlen=50000),
            'states': [],  # List[Dict[int, StateValue]]
        }
        self._max_buffer_size = 50000

        # 握手信息
        self._handshake: HandshakeInfo = None

        # 状态标志
        self._is_paused = False

        # 初始化UI
        self._setup_ui()
        self._setup_connections()
        self._setup_timers()
        
        # 初始化串口列表
        self._control_panel.serial_panel.refresh_ports()

        # 初始化自动更新器
        self._updater = AutoUpdater(self)

        # 启动时静默检查更新
        QTimer.singleShot(2000, lambda: self._updater.check_for_updates(silent=True))

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("控制系统实时分析工具 v2.0")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        self._setup_styles()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 模式切换工具栏
        self._setup_mode_toolbar(main_layout)
        
        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)
        
        # 左侧控制面板
        self._control_panel = UnifiedControlPanel()
        content_layout.addWidget(self._control_panel)
        
        # ★ 右侧图表区域 - 统一使用 SimulatorPlotWidget（支持状态选择）
        self._plot_widget = SimulatorPlotWidget()
        content_layout.addWidget(self._plot_widget, stretch=1)

        main_layout.addLayout(content_layout, stretch=1)
        
        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪 - 请选择数据源并连接")
        
        self._setup_menu()
    
    def _setup_styles(self):
        """设置全局样式"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QWidget { color: #CCCCCC; font-family: "Microsoft YaHei", sans-serif; }
            QLabel { color: #CCCCCC; }
            QComboBox {
                background-color: #3C3C3C; color: #FFFFFF;
                border: 1px solid #555555; border-radius: 3px; padding: 4px;
            }
            QComboBox:hover { border-color: #0078D4; }
            QComboBox QAbstractItemView {
                background-color: #2D2D30; color: #FFFFFF;
                selection-background-color: #0078D4;
            }
            QStatusBar { background-color: #007ACC; color: white; }
            QRadioButton { color: #FFFFFF; font-weight: bold; padding: 8px 16px; }
            QRadioButton::indicator { width: 0px; height: 0px; }
        """)
    
    def _setup_mode_toolbar(self, parent_layout):
        """设置模式切换工具栏"""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame { background-color: #2D2D30; border-bottom: 1px solid #3D3D3D; }
        """)
        toolbar_frame.setFixedHeight(45)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(5)
        
        title_label = QLabel("数据源:")
        title_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        toolbar_layout.addWidget(title_label)
        
        self._mode_group = QButtonGroup(self)
        
        # 串口模式按钮
        self._serial_mode_btn = QRadioButton("🔌 串口")
        self._serial_mode_btn.setChecked(True)
        self._serial_mode_btn.setStyleSheet("""
            QRadioButton { background-color: #3C3C3C; border-radius: 3px; padding: 6px 12px; }
            QRadioButton:hover { background-color: #4C4C4C; }
            QRadioButton:checked { background-color: #0E639C; border: 2px solid #4FC3F7; }
        """)
        self._mode_group.addButton(self._serial_mode_btn, DataSourceMode.SERIAL)
        toolbar_layout.addWidget(self._serial_mode_btn)
        
        # 仿真模式按钮
        self._simulator_mode_btn = QRadioButton("📡 UDP仿真")
        self._simulator_mode_btn.setStyleSheet("""
            QRadioButton { background-color: #3C3C3C; border-radius: 3px; padding: 6px 12px; }
            QRadioButton:hover { background-color: #4C4C4C; }
            QRadioButton:checked { background-color: #388E3C; border: 2px solid #81C784; }
        """)
        self._mode_group.addButton(self._simulator_mode_btn, DataSourceMode.SIMULATOR)
        toolbar_layout.addWidget(self._simulator_mode_btn)
        
        self._mode_group.idClicked.connect(self._on_mode_changed)
        
        toolbar_layout.addStretch()
        
        self._mode_indicator = QLabel("当前: 串口模式")
        self._mode_indicator.setStyleSheet("color: #4FC3F7; font-size: 11px;")
        toolbar_layout.addWidget(self._mode_indicator)
        
        parent_layout.addWidget(toolbar_frame)
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background-color: #2D2D30; color: #CCCCCC; }
            QMenuBar::item:selected { background-color: #3D3D3D; }
            QMenu { background-color: #2D2D30; color: #CCCCCC; border: 1px solid #3D3D3D; }
            QMenu::item:selected { background-color: #0078D4; }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        export_action = QAction("导出数据(&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        clear_action = QAction("清空数据(&C)", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self._clear_data)
        view_menu.addAction(clear_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        update_action = QAction("检查更新(&U)", self)
        update_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(update_action)
        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        protocol_action = QAction("串口协议说明(&P)", self)
        protocol_action.triggered.connect(self._show_protocol_help)
        help_menu.addAction(protocol_action)

    def _setup_connections(self):
        """设置信号连接"""
        # ============ 串口模式信号 ============
        self._control_panel.serial_panel.connect_requested.connect(self._connect_serial)
        self._control_panel.serial_panel.disconnect_requested.connect(self._disconnect_serial)
        
        self._serial_manager.data_received.connect(self._on_data_received)
        self._serial_manager.handshake_received.connect(self._on_handshake_received)
        self._serial_manager.connection_changed.connect(self._on_serial_connection_changed)
        self._serial_manager.error_occurred.connect(self._on_error)

        # ============ 仿真模式信号 ============
        self._control_panel.simulator_panel.connect_requested.connect(self._connect_simulator)
        self._control_panel.simulator_panel.disconnect_requested.connect(self._disconnect_simulator)
        
        self._simulator_receiver.data_received.connect(self._on_data_received)
        self._simulator_receiver.handshake_received.connect(self._on_handshake_received)
        self._simulator_receiver.connection_changed.connect(self._on_simulator_connection_changed)
        self._simulator_receiver.error_occurred.connect(self._on_error)

        # ============ 共用控件信号 ============
        self._control_panel.pid_panel.send_requested.connect(self._send_pid_params)
        self._control_panel.setpoint_panel.send_requested.connect(self._send_setpoint)
        self._control_panel.data_panel.clear_requested.connect(self._clear_data)
        self._control_panel.data_panel.pause_requested.connect(self._set_paused)
        self._control_panel.data_panel.export_requested.connect(self._export_data)

    def _setup_timers(self):
        """设置定时器"""
        # 图表更新定时器
        self._plot_timer = QTimer()
        self._plot_timer.timeout.connect(self._update_plots)
        self._plot_timer.start(50)  # 20 FPS

        # 性能指标更新定时器
        self._metrics_timer = QTimer()
        self._metrics_timer.timeout.connect(self._update_metrics)
        self._metrics_timer.start(500)
        
        # FFT更新定时器
        self._fft_timer = QTimer()
        self._fft_timer.timeout.connect(self._update_fft)
        self._fft_timer.start(1000)

    # ============ 模式切换 ============
    
    def _on_mode_changed(self, mode_id: int):
        """模式切换"""
        if mode_id == self._current_mode:
            return
        
        # 断开当前连接
        if self._current_mode == DataSourceMode.SERIAL and self._serial_manager.is_connected:
            self._serial_manager.disconnect()
        elif self._current_mode == DataSourceMode.SIMULATOR and self._simulator_receiver.is_connected:
            self._simulator_receiver.stop()
        
        self._current_mode = mode_id
        self._control_panel.set_mode(mode_id)

        # 清空数据
        self._clear_data()

        # 更新UI
        if mode_id == DataSourceMode.SERIAL:
            self._mode_indicator.setText("当前: 串口模式")
            self._mode_indicator.setStyleSheet("color: #4FC3F7; font-size: 11px;")
            self._status_bar.showMessage("已切换到串口模式 - 请连接串口")
        else:
            self._mode_indicator.setText("当前: UDP仿真模式")
            self._mode_indicator.setStyleSheet("color: #81C784; font-size: 11px;")
            self._status_bar.showMessage("已切换到UDP仿真模式 - 请开始监听")

    # ============ 连接管理 ============

    def _connect_serial(self, port: str, baudrate: int):
        """连接串口"""
        self._status_bar.showMessage(f"正在连接 {port}...")
        if self._serial_manager.connect(port, baudrate):
            self._status_bar.showMessage(f"已连接 {port} @ {baudrate}")
        else:
            self._status_bar.showMessage("连接失败")
            QMessageBox.warning(self, "连接失败", f"无法连接到 {port}")
    
    def _disconnect_serial(self):
        """断开串口"""
        self._serial_manager.disconnect()
        self._plot_widget.clear_state_definitions()
        self._status_bar.showMessage("已断开连接")
    
    def _connect_simulator(self, host: str, port: int):
        """连接UDP仿真"""
        self._status_bar.showMessage(f"正在监听 {host}:{port}...")
        self._simulator_receiver.start(host, port)
    
    def _disconnect_simulator(self):
        """断开UDP仿真"""
        self._simulator_receiver.stop()
        self._plot_widget.clear_state_definitions()
        self._status_bar.showMessage("已停止监听")
    
    def _on_serial_connection_changed(self, connected: bool):
        """串口连接状态改变"""
        self._control_panel.serial_panel.set_connected(connected)
        if not connected:
            self._plot_widget.clear_state_definitions()

    def _on_simulator_connection_changed(self, connected: bool, message: str):
        """仿真连接状态改变"""
        self._control_panel.simulator_panel.set_connected(connected, message)
        if connected:
            self._status_bar.showMessage(message)
        else:
            self._plot_widget.clear_state_definitions()

    def _on_error(self, message: str):
        """错误处理"""
        self._status_bar.showMessage(f"错误: {message}")

    # ============ 数据处理 (统一) ============

    def _on_handshake_received(self, handshake: HandshakeInfo):
        """收到握手帧 - 两种模式共用"""
        # ★ 检查状态定义是否变化（避免周期性握手帧导致数据清空）
        state_changed = False
        if self._handshake is None:
            # 首次收到握手帧
            state_changed = True
        elif self._handshake.state_count != handshake.state_count:
            # 状态数量变化
            state_changed = True
        elif self._handshake.source != handshake.source:
            # 数据源变化
            state_changed = True
        else:
            # 检查状态名称是否变化
            old_names = [s.name for s in self._handshake.state_defs]
            new_names = [s.name for s in handshake.state_defs]
            if old_names != new_names:
                state_changed = True

        self._handshake = handshake

        # 显示握手信息
        state_names = [s.name for s in handshake.state_defs]
        source_name = "串口" if handshake.source == "serial" else "UDP仿真"
        self._status_bar.showMessage(
            f"已连接 [{source_name}] 协议v{handshake.protocol_version}, "
            f"{handshake.state_count}个状态: {', '.join(state_names)}"
        )

        # 更新控制面板
        if self._current_mode == DataSourceMode.SIMULATOR:
            self._control_panel.simulator_panel.set_system_type(
                handshake.source.replace('udp:', ''),
                handshake.protocol_version,
                handshake.state_count
            )

        # ★ 只在状态定义变化时才更新图表组件和清空数据
        if state_changed:
            state_defs_list = [
                {
                    'index': s.index,
                    'name': s.name,
                    'unit': s.unit,
                    'description': s.description
                }
                for s in handshake.state_defs
            ]
            self._plot_widget.set_state_definitions(state_defs_list)
            # 清空旧数据
            self._clear_data()

    def _on_data_received(self, data: UnifiedData):
        """收到数据 - 两种模式共用"""
        if self._is_paused:
            return
        
        # 检测时间戳重置
        if len(self._data_buffer['timestamps']) > 0:
            last_time = self._data_buffer['timestamps'][-1]
            if data.timestamp < last_time - 0.5:
                self._clear_data()
                self._status_bar.showMessage("检测到数据重置，已清空缓冲区")

        # 存储数据
        self._data_buffer['timestamps'].append(data.timestamp)

        # 存储所有状态
        states_dict = {}
        for i, state in enumerate(data.states):
            states_dict[i] = {'target': state.target, 'current': state.current}
        self._data_buffer['states'].append(states_dict)

        # 限制缓冲区大小
        if len(self._data_buffer['states']) > self._max_buffer_size:
            self._data_buffer['states'].pop(0)

        # 更新数据点数
        self._control_panel.data_panel.set_data_count(len(self._data_buffer['timestamps']))

    def _update_plots(self):
        """更新图表"""
        if self._is_paused:
            return
        
        if len(self._data_buffer['timestamps']) == 0:
            return
        
        n = min(2000, len(self._data_buffer['timestamps']))
        timestamps = np.array(list(self._data_buffer['timestamps']))[-n:]

        # 获取用户选择的状态索引
        selected_idx = self._plot_widget.get_selected_state_index()

        # 提取选中状态的数据
        setpoints = []
        process_values = []
        for state_dict in self._data_buffer['states'][-n:]:
            if selected_idx in state_dict:
                setpoints.append(state_dict[selected_idx]['target'])
                process_values.append(state_dict[selected_idx]['current'])
            else:
                setpoints.append(0.0)
                process_values.append(0.0)

        setpoints = np.array(setpoints)
        process_values = np.array(process_values)
        errors = setpoints - process_values

        # 控制输出：如果有多个状态，使用最后一个
        outputs = np.zeros_like(timestamps)
        if self._data_buffer['states'] and len(self._data_buffer['states'][-1]) > 1:
            last_idx = max(self._data_buffer['states'][-1].keys())
            for i, state_dict in enumerate(self._data_buffer['states'][-n:]):
                if last_idx in state_dict:
                    outputs[i] = state_dict[last_idx]['current']

        self._plot_widget.standard_plot.update_data(
            timestamps, setpoints, process_values, errors, outputs
        )

    def _update_metrics(self):
        """更新性能指标"""
        if self._is_paused or len(self._data_buffer['timestamps']) < 10:
            return
        
        selected_idx = self._plot_widget.get_selected_state_index()
        n = len(self._data_buffer['timestamps'])

        timestamps = np.array(list(self._data_buffer['timestamps']))
        setpoints = np.array([
            s.get(selected_idx, {}).get('target', 0.0)
            for s in self._data_buffer['states']
        ])
        process_values = np.array([
            s.get(selected_idx, {}).get('current', 0.0)
            for s in self._data_buffer['states']
        ])
        errors = setpoints - process_values

        metrics = self._analyzer.analyze(timestamps, setpoints, process_values, errors)
        self._control_panel.metrics_panel.update_serial_metrics(metrics)

    def _update_fft(self):
        """更新FFT"""
        if self._is_paused or len(self._data_buffer['timestamps']) < 64:
            return
        
        selected_idx = self._plot_widget.get_selected_state_index()
        n = min(4096, len(self._data_buffer['timestamps']))

        timestamps = np.array(list(self._data_buffer['timestamps']))[-n:]
        setpoints = np.array([
            s.get(selected_idx, {}).get('target', 0.0)
            for s in self._data_buffer['states'][-n:]
        ])
        process_values = np.array([
            s.get(selected_idx, {}).get('current', 0.0)
            for s in self._data_buffer['states'][-n:]
        ])
        errors = setpoints - process_values

        freq, mag = self._analyzer.compute_fft(timestamps, errors)
        if len(freq) > 0:
            self._plot_widget.standard_plot.update_fft(freq, mag)

    # ============ 控制命令 ============

    def _send_pid_params(self, kp: float, ki: float, kd: float):
        """发送PID参数"""
        if self._current_mode == DataSourceMode.SERIAL and self._serial_manager.is_connected:
            cmd = f"PID:{kp:.4f},{ki:.4f},{kd:.4f}"
            self._serial_manager.send(cmd)
            self._status_bar.showMessage(f"已发送: {cmd}")
        else:
            self._status_bar.showMessage("未连接，无法发送")

    def _send_setpoint(self, setpoint: float):
        """发送设定值"""
        if self._current_mode == DataSourceMode.SERIAL and self._serial_manager.is_connected:
            cmd = f"SP:{setpoint:.2f}"
            self._serial_manager.send(cmd)
            self._status_bar.showMessage(f"已发送: {cmd}")
        else:
            self._status_bar.showMessage("未连接，无法发送")

    # ============ 数据管理 ============

    def _set_paused(self, paused: bool):
        """设置暂停状态"""
        self._is_paused = paused
        self._status_bar.showMessage("已暂停" if paused else "继续运行")
    
    def _clear_data(self):
        """清空数据"""
        self._data_buffer['timestamps'].clear()
        self._data_buffer['states'].clear()
        self._plot_widget.clear_all()
        self._control_panel.data_panel.set_data_count(0)
        self._control_panel.metrics_panel.clear()
        self._status_bar.showMessage("数据已清空")

    def _export_data(self):
        """导出数据"""
        if len(self._data_buffer['timestamps']) == 0:
            QMessageBox.information(self, "导出", "没有数据可导出")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "control_data.csv", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入表头
                if self._handshake:
                    headers = ["时间(s)"]
                    for s in self._handshake.state_defs:
                        headers.append(f"{s.name}_目标")
                        headers.append(f"{s.name}_当前")
                    f.write(",".join(headers) + "\n")
                else:
                    f.write("时间(s),状态\n")

                # 写入数据
                timestamps = list(self._data_buffer['timestamps'])
                states = self._data_buffer['states']
                for i, t in enumerate(timestamps):
                    row = [f"{t:.4f}"]
                    if i < len(states):
                        for idx in sorted(states[i].keys()):
                            row.append(f"{states[i][idx]['target']:.4f}")
                            row.append(f"{states[i][idx]['current']:.4f}")
                    f.write(",".join(row) + "\n")

            self._status_bar.showMessage(f"已导出到 {file_path}")
            QMessageBox.information(self, "导出成功", f"已导出 {len(timestamps)} 条数据")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))
    
    def _show_about(self):
        """显示关于"""
        version = get_current_version()
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            f"<div style='color: #000000;'>"
            f"<h3 style='color: #1565C0;'>控制系统实时分析工具 v{version}</h3>"
            "<p>统一架构版本 - 串口和仿真共用核心组件</p>"
            "<h4 style='color: #2E7D32;'>数据源:</h4>"
            "<ul>"
            "<li><b>串口</b>: 高效文本协议，适合单片机</li>"
            "<li><b>UDP仿真</b>: JSON协议，适合仿真器</li>"
            "</ul>"
            "<h4 style='color: #2E7D32;'>主要功能:</h4>"
            "<ul>"
            "<li>实时数据可视化</li>"
            "<li>多状态变量选择</li>"
            "<li>FFT频谱分析</li>"
            "<li>性能指标计算</li>"
            "</ul>"
            "<p style='color: #666;'>GitHub: ktkuri132/Control_System_Box</p>"
            "</div>"
        )
        msg.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #000000; }")
        msg.exec()

    def _show_protocol_help(self):
        """显示串口协议帮助"""
        msg = QMessageBox(self)
        msg.setWindowTitle("串口协议说明")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            "<div style='color: #000000;'>"
            "<h3 style='color: #1565C0;'>串口数据协议</h3>"
            "<h4 style='color: #D84315;'>【握手帧】首次连接发送</h4>"
            "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>#H,状态数,名称1,名称2,...\\n</pre>"
            "<p>示例: <code style='background-color: #E3F2FD; padding: 2px;'>#H,3,angle,position,force</code></p>"
            "<h4 style='color: #D84315;'>【数据帧】高频发送</h4>"
            "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>#D,序号,时间ms,目标1,当前1,目标2,当前2,...\\n</pre>"
            "<p>示例: <code style='background-color: #E3F2FD; padding: 2px;'>#D,1234,15000,0.00,0.05,0.00,-0.02</code></p>"
            "<h4 style='color: #D84315;'>【简化数据帧】目标值不变时</h4>"
            "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>#d,序号,时间ms,当前1,当前2,...\\n</pre>"
            "<p>示例: <code style='background-color: #E3F2FD; padding: 2px;'>#d,1234,15000,0.05,-0.02</code></p>"
            "<h4 style='color: #D84315;'>【旧格式兼容】</h4>"
            "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>SP:100,PV:95.5,OUT:50</pre>"
            "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>100,95.5,50</pre>"
            "</div>"
        )
        msg.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #000000; }")
        msg.exec()

    def _check_for_updates(self):
        """手动检查更新"""
        self._updater.check_for_updates(silent=False)

    def closeEvent(self, event):
        """窗口关闭"""
        if self._serial_manager.is_connected:
            self._serial_manager.disconnect()
        if self._simulator_receiver.is_connected:
            self._simulator_receiver.stop()
        event.accept()
