"""
主窗口 (统一架构版本)
串口和仿真模式共用相同的核心组件
唯一区别是数据接收方式不同
"""
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStatusBar, QMessageBox, QFileDialog,
    QStackedWidget, QButtonGroup, QRadioButton,
    QFrame, QLabel
)
from PyQt6.QtCore import QTimer, Qt, QObject, pyqtSignal
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
from core.signal_filter import (
    get_filter, set_all_filters_enabled, set_all_filters_type,
    set_all_filters_strength, reset_all_filters, HarmonicAnalyzer
)
# 使用多进程处理器以充分利用多核 CPU
from core.multiprocess_processor import (
    MultiProcessDataProcessor, HighPerformanceBuffer,
    PlotUpdateThrottler, DataDownsampler
)
# 调试性能分析器
from core.debug_profiler import (
    DEBUG_MODE, profile_method, ProfileBlock,
    start_profiling, stop_profiling, print_performance_report, get_profiler
)


class DataProcessedSignalBridge(QObject):
    """信号桥接器 - 用于从工作线程安全地发送数据到主线程"""
    data_ready = pyqtSignal(object)  # 使用 object 类型更兼容


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
        
        # ★ 高性能数据缓冲区 - 两种模式共用
        self._data_buffer = HighPerformanceBuffer(max_size=50000)

        # 绑图更新节流器
        self._plot_throttler = PlotUpdateThrottler(min_interval_ms=50)  # 20 FPS

        # ★ 信号桥接器 - 用于线程安全的数据传递
        self._signal_bridge = DataProcessedSignalBridge()
        self._signal_bridge.data_ready.connect(self._on_data_processed)

        # ★ 多进程数据处理器 - 充分利用多核 CPU
        self._data_processor = MultiProcessDataProcessor()
        self._data_processor.set_callback(self._on_data_processed_from_worker)
        self._data_processor.start()

        # 握手信息
        self._handshake: HandshakeInfo = None

        # 状态标志
        self._is_paused = False

        # 谐波分析器
        self._harmonic_analyzer = HarmonicAnalyzer(sample_rate=100.0)

        # 初始化UI
        self._setup_ui()
        self._setup_connections()
        self._setup_timers()
        
        # 初始化串口列表
        self._control_panel.serial_panel.refresh_ports()

        # 连接滤波面板信号
        self._control_panel.filter_panel.filter_changed.connect(self._on_filter_changed)

        # 初始化自动更新器
        self._updater = AutoUpdater(self)

        # 启动时静默检查更新
        QTimer.singleShot(2000, lambda: self._updater.check_for_updates(silent=True))

        # ★ 调试模式：启动性能监控
        if DEBUG_MODE:
            start_profiling()
            # 定时打印性能报告
            self._debug_timer = QTimer()
            self._debug_timer.timeout.connect(print_performance_report)
            self._debug_timer.start(10000)  # 每 10 秒打印一次

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("控制系统实时分析工具 v2.1.2")
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
        if len(self._data_buffer) > 0:
            timestamps, _ = self._data_buffer.get_data(1)
            if len(timestamps) > 0 and data.timestamp < timestamps[-1] - 0.5:
                self._clear_data()
                self._status_bar.showMessage("检测到数据重置，已清空缓冲区")

        # 存储所有状态
        states_dict = {}
        for i, state in enumerate(data.states):
            states_dict[i] = {'target': state.target, 'current': state.current}

        # 使用高性能缓冲区存储
        self._data_buffer.append(data.timestamp, states_dict)

        # 更新数据点数
        self._control_panel.data_panel.set_data_count(len(self._data_buffer))

    def _update_plots(self):
        """更新图表 - 使用节流和多进程优化"""
        if self._is_paused:
            return
        
        # 节流检查
        if not self._plot_throttler.should_update():
            return

        buffer_len = len(self._data_buffer)
        if buffer_len == 0:
            return
        
        with ProfileBlock("update_plots.get_data"):
            # 限制绑图数据点数
            n = min(3000, buffer_len)  # 多进程可以处理更多数据
            timestamps, states = self._data_buffer.get_data(n)

        if len(timestamps) == 0:
            return

        # 获取用户选择的状态索引
        selected_idx = self._plot_widget.get_selected_state_index()

        # 获取滤波器设置
        signal_filter = get_filter(selected_idx)
        filter_enabled = signal_filter.enabled

        # 设置多进程处理器的滤波参数
        if filter_enabled:
            self._data_processor.set_filter(
                signal_filter.get_filter_type_key(),  # 使用英文键名
                signal_filter.strength / 10.0,  # 转换为 0-1 范围
                signal_filter.window_size
            )
            self._plot_widget.standard_plot.set_show_raw(True)
        else:
            self._data_processor.set_filter('none', 0.3, 5)
            self._plot_widget.standard_plot.set_show_raw(False)

        # 提交给多进程处理（非阻塞）
        self._data_processor.submit_task(timestamps, states, selected_idx)

    def _on_data_processed_from_worker(self, result: dict):
        """
        多进程处理完成回调（在工作线程中调用）
        通过 Qt 信号安全地转发到主线程
        """
        # 使用信号桥接器安全地发送到主线程
        try:
            self._signal_bridge.data_ready.emit(result)
        except Exception as e:
            print(f"[MainWindow] 发送信号失败: {e}")

    @profile_method
    def _on_data_processed(self, result: dict):
        """后台处理完成回调（在主线程中执行）"""
        try:
            timestamps = result['timestamps']
            setpoints = result['setpoints']
            process_values = result['process_values']
            raw_values = result['raw_values']
            errors = result['errors']
            outputs = result['outputs']

            with ProfileBlock("plot_update"):
                # 多进程处理器已经做了降采样，直接更新图表
                self._plot_widget.standard_plot.update_data(
                    timestamps, setpoints, process_values, errors, outputs, raw_values
                )
        except Exception as e:
            print(f"[MainWindow] 更新图表失败: {e}")
            import traceback
            traceback.print_exc()

    def _update_metrics(self):
        """更新性能指标"""
        if self._is_paused or len(self._data_buffer) < 10:
            return
        
        selected_idx = self._plot_widget.get_selected_state_index()
        timestamps, states = self._data_buffer.get_data()

        if len(timestamps) < 10:
            return

        # 提取数据
        setpoints = np.array([
            s.get(selected_idx, {}).get('target', 0.0)
            for s in states
        ])
        process_values = np.array([
            s.get(selected_idx, {}).get('current', 0.0)
            for s in states
        ])
        errors = setpoints - process_values

        metrics = self._analyzer.analyze(timestamps, setpoints, process_values, errors)
        self._control_panel.metrics_panel.update_serial_metrics(metrics)

    def _update_fft(self):
        """更新FFT和谐波分析"""
        if self._is_paused or len(self._data_buffer) < 64:
            return
        
        selected_idx = self._plot_widget.get_selected_state_index()
        n = min(4096, len(self._data_buffer))
        timestamps, states = self._data_buffer.get_data(n)

        if len(timestamps) < 64:
            return

        # 高效提取数据
        process_values = np.array([
            s.get(selected_idx, {}).get('current', 0.0)
            for s in states
        ])
        setpoints = np.array([
            s.get(selected_idx, {}).get('target', 0.0)
            for s in states
        ])
        errors = setpoints - process_values

        # 更新FFT图
        freq, mag = self._analyzer.compute_fft(timestamps, errors)
        if len(freq) > 0:
            self._plot_widget.standard_plot.update_fft(freq, mag)

        # 谐波分析 - 对原始测量值进行
        if len(process_values) >= 64:
            # 估算采样率
            if len(timestamps) > 1:
                dt = np.mean(np.diff(timestamps))
                if dt > 0:
                    self._harmonic_analyzer.sample_rate = 1.0 / dt

            # 执行谐波分析
            analysis = self._harmonic_analyzer.analyze(process_values)

            # 更新滤波面板的谐波显示
            self._control_panel.filter_panel.update_harmonic_analysis(analysis)

    def _on_filter_changed(self):
        """滤波设置变化时的处理"""
        # 重置所有滤波器状态
        reset_all_filters()
        self._status_bar.showMessage("滤波设置已更新")

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
        self._data_buffer.clear()
        reset_all_filters()
        self._plot_widget.clear_all()
        self._control_panel.data_panel.set_data_count(0)
        self._control_panel.metrics_panel.clear()
        self._status_bar.showMessage("数据已清空")

    def _export_data(self):
        """导出数据"""
        if len(self._data_buffer) == 0:
            QMessageBox.information(self, "导出", "没有数据可导出")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "control_data.csv", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            timestamps, states = self._data_buffer.get_data()

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
        # ★ 调试模式：打印最终性能报告并停止监控
        if DEBUG_MODE:
            print("\n=== 程序关闭，打印最终性能报告 ===")
            print_performance_report()
            print("\n瓶颈分析:")
            print(get_profiler().get_bottleneck_analysis())
            stop_profiling()

        # 停止多进程数据处理器
        self._data_processor.stop()

        if self._serial_manager.is_connected:
            self._serial_manager.disconnect()
        if self._simulator_receiver.is_connected:
            self._simulator_receiver.stop()
        event.accept()
