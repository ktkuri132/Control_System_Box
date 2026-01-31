"""
统一控制面板
将两种模式的控制面板合并，共用相同组件，专用部分按需显示
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QSlider, QDial, QFrame, QCheckBox,
    QLineEdit, QStackedWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.control_panel import (
    StyledGroupBox, DialWithLabel, SliderWithLabel,
    SerialConfigPanel, PIDControlPanel, SetpointPanel, 
    MetricsPanel, DataControlPanel
)
from ui.filter_panel import FilterControlPanel


class SimulatorConfigPanel(StyledGroupBox):
    """仿真数据接收配置面板 (UDP)"""
    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("仿真数据接收 (UDP)", parent)
        self._is_connected = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(8)
        
        # IP地址
        layout.addWidget(QLabel("IP地址:"), 0, 0)
        self._host_edit = QLineEdit("127.0.0.1")
        self._host_edit.setPlaceholderText("127.0.0.1")
        layout.addWidget(self._host_edit, 0, 1, 1, 2)
        
        # 端口
        layout.addWidget(QLabel("端口:"), 1, 0)
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1024, 65535)
        self._port_spin.setValue(5555)
        layout.addWidget(self._port_spin, 1, 1, 1, 2)
        
        # 连接按钮
        self._connect_btn = QPushButton("开始监听")
        self._connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
        """)
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self._connect_btn, 2, 0, 1, 3)
        
        # 状态显示
        self._status_label = QLabel("● 未连接")
        self._status_label.setStyleSheet("color: #FF6B6B;")
        layout.addWidget(self._status_label, 3, 0, 1, 3)
        
        # 系统类型显示
        self._system_label = QLabel("系统类型: --")
        self._system_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self._system_label, 4, 0, 1, 3)
    
    def _on_connect_clicked(self):
        if self._is_connected:
            self.disconnect_requested.emit()
        else:
            host = self._host_edit.text().strip() or "127.0.0.1"
            port = self._port_spin.value()
            self.connect_requested.emit(host, port)
    
    def set_connected(self, connected: bool, message: str = ""):
        self._is_connected = connected
        if connected:
            self._connect_btn.setText("停止监听")
            self._connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E53935;
                }
            """)
            self._status_label.setText(f"● {message or '已连接'}")
            self._status_label.setStyleSheet("color: #4CAF50;")
            self._host_edit.setEnabled(False)
            self._port_spin.setEnabled(False)
        else:
            self._connect_btn.setText("开始监听")
            self._connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0E639C;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1177BB;
                }
            """)
            self._status_label.setText(f"● {message or '未连接'}")
            self._status_label.setStyleSheet("color: #FF6B6B;")
            self._host_edit.setEnabled(True)
            self._port_spin.setEnabled(True)
    
    def set_system_type(self, system_type: str, version: str = "2.0", state_count: int = 0):
        """设置系统类型信息"""
        type_names = {
            'inverted_pendulum': '倒立摆系统',
            'ball_on_plate': '滚球控制系统',
            'unknown': '未知系统'
        }
        name = type_names.get(system_type, system_type)
        if state_count > 0:
            self._system_label.setText(f"系统: {name} | 协议 v{version} | {state_count} 个状态")
        else:
            self._system_label.setText(f"系统类型: {name}")


class UnifiedMetricsPanel(StyledGroupBox):
    """统一性能指标面板 - 自动根据模式显示相应指标"""
    
    MODE_SERIAL = "serial"
    MODE_PENDULUM = "pendulum"
    MODE_BALL = "ball"
    
    def __init__(self, parent=None):
        super().__init__("性能指标", parent)
        self._current_mode = self.MODE_SERIAL
        self._metrics = {}
        self._setup_ui()
    
    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(5)
        
        # 堆叠widget用于切换不同模式的指标
        self._stack = QStackedWidget()
        self._layout.addWidget(self._stack)
        
        # 串口模式指标
        self._serial_widget = self._create_serial_metrics()
        self._stack.addWidget(self._serial_widget)
        
        # 倒立摆指标
        self._pendulum_widget = self._create_pendulum_metrics()
        self._stack.addWidget(self._pendulum_widget)
        
        # 滚球指标
        self._ball_widget = self._create_ball_metrics()
        self._stack.addWidget(self._ball_widget)
    
    def _create_metrics_grid(self, metrics_config: list) -> QWidget:
        """创建指标网格"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        for i, (key, name, unit) in enumerate(metrics_config):
            row, col = divmod(i, 2)
            
            name_label = QLabel(f"{name}:")
            name_label.setStyleSheet("color: #AAAAAA; font-size: 10px;")
            
            value_label = QLabel("--")
            value_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #888888; font-size: 10px;")
            unit_label.setFixedWidth(25)
            
            layout.addWidget(name_label, row, col * 3)
            layout.addWidget(value_label, row, col * 3 + 1)
            layout.addWidget(unit_label, row, col * 3 + 2)
            
            self._metrics[key] = value_label
        
        return widget
    
    def _create_serial_metrics(self) -> QWidget:
        """串口模式性能指标"""
        config = [
            ("rise_time", "上升时间", "s"),
            ("settling_time", "调节时间", "s"),
            ("overshoot", "超调量", "%"),
            ("peak_time", "峰值时间", "s"),
            ("steady_state_error", "稳态误差", ""),
            ("oscillation_count", "振荡次数", ""),
            ("rms_error", "RMS误差", ""),
            ("iae", "IAE", ""),
        ]
        return self._create_metrics_grid(config)
    
    def _create_pendulum_metrics(self) -> QWidget:
        """倒立摆指标"""
        config = [
            ("angle", "当前角度", "°"),
            ("cart_pos", "小车位置", "m"),
            ("force", "控制力", "N"),
            ("max_angle", "最大偏角", "°"),
            ("angular_vel", "角速度", "°/s"),
            ("settling", "稳定性", ""),
        ]
        return self._create_metrics_grid(config)
    
    def _create_ball_metrics(self) -> QWidget:
        """滚球系统指标"""
        config = [
            ("error", "位置误差", "mm"),
            ("ball_pos", "小球位置", ""),
            ("plate_angle", "平板角度", "°"),
            ("max_error", "最大误差", "mm"),
            ("track_error", "跟踪误差", "mm"),
            ("settling", "稳定性", ""),
        ]
        return self._create_metrics_grid(config)
    
    def set_mode(self, mode: str):
        """设置显示模式"""
        self._current_mode = mode
        if mode == self.MODE_SERIAL:
            self._stack.setCurrentIndex(0)
        elif mode == self.MODE_PENDULUM:
            self._stack.setCurrentIndex(1)
        elif mode == self.MODE_BALL:
            self._stack.setCurrentIndex(2)
    
    def update_serial_metrics(self, metrics):
        """更新串口模式指标"""
        def fmt(val, precision=3):
            if val is None:
                return "--"
            if isinstance(val, int):
                return str(val)
            return f"{val:.{precision}f}"
        
        self._metrics.get("rise_time", QLabel()).setText(fmt(metrics.rise_time))
        self._metrics.get("settling_time", QLabel()).setText(fmt(metrics.settling_time))
        self._metrics.get("overshoot", QLabel()).setText(fmt(metrics.overshoot, 1))
        self._metrics.get("peak_time", QLabel()).setText(fmt(metrics.peak_time))
        self._metrics.get("steady_state_error", QLabel()).setText(fmt(metrics.steady_state_error))
        self._metrics.get("oscillation_count", QLabel()).setText(str(metrics.oscillation_count))
        self._metrics.get("rms_error", QLabel()).setText(fmt(metrics.rms_error))
        self._metrics.get("iae", QLabel()).setText(fmt(metrics.iae))
    
    def update_pendulum_metrics(self, angle: float, cart_pos: float, 
                                 force: float, max_angle: float,
                                 angular_vel: float = 0.0, settling: str = "--"):
        """更新倒立摆指标"""
        self._metrics.get("angle", QLabel()).setText(f"{angle:.2f}")
        self._metrics.get("cart_pos", QLabel()).setText(f"{cart_pos:.3f}")
        self._metrics.get("force", QLabel()).setText(f"{force:.1f}")
        self._metrics.get("max_angle", QLabel()).setText(f"{max_angle:.2f}")
        self._metrics.get("angular_vel", QLabel()).setText(f"{angular_vel:.1f}")
        self._metrics.get("settling", QLabel()).setText(settling)
    
    def update_ball_metrics(self, error: float, ball_x: float, ball_y: float,
                            plate_x: float, plate_y: float, max_error: float,
                            track_error: float = 0.0, settling: str = "--"):
        """更新滚球系统指标"""
        self._metrics.get("error", QLabel()).setText(f"{error:.1f}")
        self._metrics.get("ball_pos", QLabel()).setText(f"({ball_x:.1f},{ball_y:.1f})")
        self._metrics.get("plate_angle", QLabel()).setText(f"({plate_x:.1f},{plate_y:.1f})")
        self._metrics.get("max_error", QLabel()).setText(f"{max_error:.1f}")
        self._metrics.get("track_error", QLabel()).setText(f"{track_error:.1f}")
        self._metrics.get("settling", QLabel()).setText(settling)
    
    def clear(self):
        """清空所有指标"""
        for label in self._metrics.values():
            if isinstance(label, QLabel):
                label.setText("--")


class UnifiedControlPanel(QWidget):
    """
    统一控制面板
    - 连接配置区：根据模式显示串口或UDP配置
    - 共用区：PID参数、设定值、数据控制
    - 指标区：统一性能指标（自动切换）
    """
    
    MODE_SERIAL = 0
    MODE_SIMULATOR = 1
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = self.MODE_SERIAL
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        # 使用滚动区域包裹，防止内容过多
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1E1E1E;
            }
            QScrollBar:vertical {
                background-color: #2D2D30;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
        """)
        
        # 内容容器
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
            }
            QLabel {
                color: #CCCCCC;
            }
        """)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # ===== 1. 连接配置区（堆叠切换）=====
        self._connection_stack = QStackedWidget()
        
        # 串口配置
        self.serial_panel = SerialConfigPanel()
        self._connection_stack.addWidget(self.serial_panel)
        
        # UDP仿真配置
        self.simulator_panel = SimulatorConfigPanel()
        self._connection_stack.addWidget(self.simulator_panel)
        
        layout.addWidget(self._connection_stack)
        
        # ===== 2. 设定值控制（共用）=====
        self.setpoint_panel = SetpointPanel()
        layout.addWidget(self.setpoint_panel)
        
        # ===== 3. PID参数调节（共用）=====
        self.pid_panel = PIDControlPanel()
        layout.addWidget(self.pid_panel)
        
        # ===== 4. 统一性能指标 =====
        self.metrics_panel = UnifiedMetricsPanel()
        layout.addWidget(self.metrics_panel)
        
        # ===== 5. 数据控制（共用）=====
        self.data_panel = DataControlPanel()
        layout.addWidget(self.data_panel)
        
        # ===== 6. 滤波控制 =====
        self.filter_panel = FilterControlPanel()
        layout.addWidget(self.filter_panel)

        # 弹簧
        layout.addStretch()
        
        scroll.setWidget(content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def set_mode(self, mode: int):
        """切换模式"""
        self._current_mode = mode
        self._connection_stack.setCurrentIndex(mode)
        
        # 更新指标面板模式
        if mode == self.MODE_SERIAL:
            self.metrics_panel.set_mode(UnifiedMetricsPanel.MODE_SERIAL)
        # 仿真模式的具体指标类型在收到数据时确定
    
    def set_simulator_system_type(self, system_type: str):
        """设置仿真系统类型（影响指标显示）"""
        self.simulator_panel.set_system_type(system_type)
        if system_type == 'inverted_pendulum':
            self.metrics_panel.set_mode(UnifiedMetricsPanel.MODE_PENDULUM)
        elif system_type == 'ball_on_plate':
            self.metrics_panel.set_mode(UnifiedMetricsPanel.MODE_BALL)
