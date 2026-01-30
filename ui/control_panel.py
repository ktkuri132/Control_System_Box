"""
控制面板组件
包含串口配置、PID参数调节、性能指标显示等
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QSlider, QDial, QFrame, QCheckBox,
    QTextEdit, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Optional


class StyledGroupBox(QGroupBox):
    """带样式的分组框"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
                color: #CCCCCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #CCCCCC;
            }
            QGroupBox QLabel {
                color: #CCCCCC;
                background-color: transparent;
            }
            QGroupBox QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
            }
            QGroupBox QSpinBox, QGroupBox QDoubleSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
            }
            QGroupBox QComboBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
            }
        """)


class DialWithLabel(QWidget):
    """带标签的旋钮控件"""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, label: str, min_val: float, max_val: float, 
                 default: float = 0.0, decimals: int = 2, parent=None):
        super().__init__(parent)
        self._decimals = decimals
        self._min = min_val
        self._max = max_val
        self._scale = 10 ** decimals
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 标签
        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        layout.addWidget(self._label)
        
        # 旋钮
        self._dial = QDial()
        self._dial.setRange(int(min_val * self._scale), int(max_val * self._scale))
        self._dial.setValue(int(default * self._scale))
        self._dial.setNotchesVisible(True)
        self._dial.setWrapping(False)
        self._dial.setFixedSize(70, 70)
        self._dial.valueChanged.connect(self._on_dial_changed)
        self._dial.setStyleSheet("""
            QDial {
                background-color: #3C3C3C;
            }
        """)
        
        dial_layout = QHBoxLayout()
        dial_layout.addStretch()
        dial_layout.addWidget(self._dial)
        dial_layout.addStretch()
        layout.addLayout(dial_layout)
        
        # 数值显示/编辑
        self._spinbox = QDoubleSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setValue(default)
        self._spinbox.setSingleStep(10 ** (-decimals))
        self._spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        layout.addWidget(self._spinbox)
    
    def _on_dial_changed(self, value: int):
        float_value = value / self._scale
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(float_value)
        self._spinbox.blockSignals(False)
        self.valueChanged.emit(float_value)
    
    def _on_spinbox_changed(self, value: float):
        self._dial.blockSignals(True)
        self._dial.setValue(int(value * self._scale))
        self._dial.blockSignals(False)
        self.valueChanged.emit(value)
    
    def value(self) -> float:
        return self._spinbox.value()
    
    def setValue(self, value: float):
        self._spinbox.setValue(value)


class SliderWithLabel(QWidget):
    """带标签的滑块控件"""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, label: str, min_val: float, max_val: float,
                 default: float = 0.0, decimals: int = 2, parent=None):
        super().__init__(parent)
        self._decimals = decimals
        self._scale = 10 ** decimals
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # 标签
        self._label = QLabel(label)
        self._label.setFixedWidth(30)
        self._label.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        layout.addWidget(self._label)
        
        # 滑块
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(int(min_val * self._scale), int(max_val * self._scale))
        self._slider.setValue(int(default * self._scale))
        self._slider.valueChanged.connect(self._on_slider_changed)
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 6px;
                background: #3C3C3C;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078D4;
                border: 1px solid #005A9E;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #1C86E5;
            }
        """)
        layout.addWidget(self._slider, stretch=1)
        
        # 数值显示
        self._spinbox = QDoubleSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setValue(default)
        self._spinbox.setFixedWidth(80)
        self._spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        layout.addWidget(self._spinbox)
    
    def _on_slider_changed(self, value: int):
        float_value = value / self._scale
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(float_value)
        self._spinbox.blockSignals(False)
        self.valueChanged.emit(float_value)
    
    def _on_spinbox_changed(self, value: float):
        self._slider.blockSignals(True)
        self._slider.setValue(int(value * self._scale))
        self._slider.blockSignals(False)
        self.valueChanged.emit(value)
    
    def value(self) -> float:
        return self._spinbox.value()
    
    def setValue(self, value: float):
        self._spinbox.setValue(value)


class SerialConfigPanel(StyledGroupBox):
    """串口配置面板"""
    connect_requested = pyqtSignal(str, int)  # (port, baudrate)
    disconnect_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("串口配置", parent)
        self._is_connected = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(8)
        
        # COM口选择
        layout.addWidget(QLabel("端口:"), 0, 0)
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        layout.addWidget(self._port_combo, 0, 1)
        
        # 刷新按钮
        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setFixedWidth(30)
        self._refresh_btn.setToolTip("刷新串口列表")
        self._refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(self._refresh_btn, 0, 2)
        
        # 波特率选择
        layout.addWidget(QLabel("波特率:"), 1, 0)
        self._baudrate_combo = QComboBox()
        self._baudrate_combo.addItems([
            "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"
        ])
        self._baudrate_combo.setCurrentText("115200")
        layout.addWidget(self._baudrate_combo, 1, 1, 1, 2)
        
        # 连接按钮
        self._connect_btn = QPushButton("连接")
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
        
        # 状态指示
        self._status_label = QLabel("● 未连接")
        self._status_label.setStyleSheet("color: #FF6B6B;")
        layout.addWidget(self._status_label, 3, 0, 1, 3)
    
    def refresh_ports(self):
        """刷新串口列表"""
        from core.serial_manager import SerialManager
        
        self._port_combo.clear()
        ports = SerialManager.get_available_ports()
        for port, description in ports:
            self._port_combo.addItem(description, port)
        
        if not ports:
            self._port_combo.addItem("未检测到串口", "")
    
    def _on_connect_clicked(self):
        if self._is_connected:
            self.disconnect_requested.emit()
        else:
            port = self._port_combo.currentData()
            if port:
                baudrate = int(self._baudrate_combo.currentText())
                self.connect_requested.emit(port, baudrate)
    
    def set_connected(self, connected: bool):
        """设置连接状态"""
        self._is_connected = connected
        if connected:
            self._connect_btn.setText("断开")
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
            self._status_label.setText("● 已连接")
            self._status_label.setStyleSheet("color: #4CAF50;")
            self._port_combo.setEnabled(False)
            self._baudrate_combo.setEnabled(False)
        else:
            self._connect_btn.setText("连接")
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
            self._status_label.setText("● 未连接")
            self._status_label.setStyleSheet("color: #FF6B6B;")
            self._port_combo.setEnabled(True)
            self._baudrate_combo.setEnabled(True)


class PIDControlPanel(StyledGroupBox):
    """PID参数控制面板"""
    pid_changed = pyqtSignal(float, float, float)  # (Kp, Ki, Kd)
    send_requested = pyqtSignal(float, float, float)  # 发送请求
    
    def __init__(self, parent=None):
        super().__init__("PID 参数调节", parent)
        self._realtime_send = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 三个旋钮水平排列
        dials_layout = QHBoxLayout()
        dials_layout.setSpacing(5)
        
        # Kp 旋钮 (比例系数，通常范围较大)
        self._kp_dial = DialWithLabel("Kp", 0.0, 100.0, 1.0, decimals=2)
        self._kp_dial.valueChanged.connect(self._on_value_changed)
        
        # Ki 旋钮 (积分系数)
        self._ki_dial = DialWithLabel("Ki", 0.0, 10.0, 0.0, decimals=3)
        self._ki_dial.valueChanged.connect(self._on_value_changed)
        
        # Kd 旋钮 (微分系数)
        self._kd_dial = DialWithLabel("Kd", 0.0, 10.0, 0.0, decimals=3)
        self._kd_dial.valueChanged.connect(self._on_value_changed)
        
        dials_layout.addWidget(self._kp_dial)
        dials_layout.addWidget(self._ki_dial)
        dials_layout.addWidget(self._kd_dial)
        
        layout.addLayout(dials_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #3D3D3D;")
        layout.addWidget(line)
        
        # 实时发送选项
        self._realtime_check = QCheckBox("实时发送")
        self._realtime_check.setStyleSheet("color: #CCCCCC;")
        self._realtime_check.toggled.connect(self._on_realtime_toggled)
        layout.addWidget(self._realtime_check)
        
        # 发送按钮
        self._send_btn = QPushButton("发送 PID 参数")
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        self._send_btn.clicked.connect(self._on_send_clicked)
        layout.addWidget(self._send_btn)
        
        # 当前参数显示
        self._params_label = QLabel("Kp=1.00, Ki=0.000, Kd=0.000")
        self._params_label.setStyleSheet("color: #888888; font-size: 10px;")
        self._params_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._params_label)
    
    def _on_value_changed(self, _):
        kp, ki, kd = self.get_values()
        self._params_label.setText(f"Kp={kp:.2f}, Ki={ki:.3f}, Kd={kd:.3f}")
        self.pid_changed.emit(kp, ki, kd)
        
        if self._realtime_send:
            self.send_requested.emit(kp, ki, kd)
    
    def _on_realtime_toggled(self, checked: bool):
        self._realtime_send = checked
        self._send_btn.setEnabled(not checked)
    
    def _on_send_clicked(self):
        kp, ki, kd = self.get_values()
        self.send_requested.emit(kp, ki, kd)
    
    def get_values(self) -> tuple[float, float, float]:
        """获取当前PID参数"""
        return (
            self._kp_dial.value(),
            self._ki_dial.value(),
            self._kd_dial.value()
        )
    
    def set_values(self, kp: float, ki: float, kd: float):
        """设置PID参数"""
        self._kp_dial.setValue(kp)
        self._ki_dial.setValue(ki)
        self._kd_dial.setValue(kd)


class MetricsPanel(StyledGroupBox):
    """性能指标显示面板"""
    
    def __init__(self, parent=None):
        super().__init__("性能指标", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(5)
        
        # 创建指标显示标签
        self._metrics = {}
        metrics_config = [
            ("rise_time", "上升时间", "s"),
            ("settling_time", "调节时间", "s"),
            ("overshoot", "超调量", "%"),
            ("peak_time", "峰值时间", "s"),
            ("steady_state_error", "稳态误差", ""),
            ("oscillation_count", "振荡次数", ""),
            ("rms_error", "RMS误差", ""),
            ("iae", "IAE", ""),
        ]
        
        for i, (key, name, unit) in enumerate(metrics_config):
            row, col = divmod(i, 2)
            
            name_label = QLabel(f"{name}:")
            name_label.setStyleSheet("color: #AAAAAA; font-size: 10px;")
            
            value_label = QLabel("--")
            value_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #888888; font-size: 10px;")
            unit_label.setFixedWidth(20)
            
            layout.addWidget(name_label, row, col * 3)
            layout.addWidget(value_label, row, col * 3 + 1)
            layout.addWidget(unit_label, row, col * 3 + 2)
            
            self._metrics[key] = value_label
    
    def update_metrics(self, metrics):
        """更新性能指标显示"""
        def format_value(val, precision=3):
            if val is None:
                return "--"
            if isinstance(val, int):
                return str(val)
            return f"{val:.{precision}f}"
        
        self._metrics["rise_time"].setText(format_value(metrics.rise_time))
        self._metrics["settling_time"].setText(format_value(metrics.settling_time))
        self._metrics["overshoot"].setText(format_value(metrics.overshoot, 1))
        self._metrics["peak_time"].setText(format_value(metrics.peak_time))
        self._metrics["steady_state_error"].setText(format_value(metrics.steady_state_error))
        self._metrics["oscillation_count"].setText(str(metrics.oscillation_count))
        self._metrics["rms_error"].setText(format_value(metrics.rms_error))
        self._metrics["iae"].setText(format_value(metrics.iae))


class SetpointPanel(StyledGroupBox):
    """设定值控制面板"""
    setpoint_changed = pyqtSignal(float)
    send_requested = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__("设定值 (Setpoint)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 设定值滑块
        self._sp_slider = SliderWithLabel("SP", 0.0, 100.0, 50.0, decimals=1)
        self._sp_slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self._sp_slider)
        
        # 发送按钮
        btn_layout = QHBoxLayout()
        
        self._send_btn = QPushButton("发送设定值")
        self._send_btn.clicked.connect(self._on_send_clicked)
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
        """)
        btn_layout.addWidget(self._send_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_value_changed(self, value: float):
        self.setpoint_changed.emit(value)
    
    def _on_send_clicked(self):
        self.send_requested.emit(self._sp_slider.value())
    
    def get_value(self) -> float:
        return self._sp_slider.value()


class DataControlPanel(StyledGroupBox):
    """数据控制面板"""
    clear_requested = pyqtSignal()
    pause_requested = pyqtSignal(bool)  # True=暂停, False=继续
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("数据控制", parent)
        self._is_paused = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # 数据点数显示
        self._count_label = QLabel("数据点数: 0")
        self._count_label.setStyleSheet("color: #AAAAAA;")
        layout.addWidget(self._count_label)
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        self._pause_btn = QPushButton("暂停")
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #FFA726;
            }
        """)
        btn_layout.addWidget(self._pause_btn)
        
        self._clear_btn = QPushButton("清空")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        btn_layout.addWidget(self._clear_btn)
        
        layout.addLayout(btn_layout)
        
        # 导出按钮
        self._export_btn = QPushButton("导出数据 (CSV)")
        self._export_btn.clicked.connect(lambda: self.export_requested.emit())
        self._export_btn.setStyleSheet("""
            QPushButton {
                background-color: #455A64;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        layout.addWidget(self._export_btn)
    
    def _on_pause_clicked(self):
        self._is_paused = not self._is_paused
        self._pause_btn.setText("继续" if self._is_paused else "暂停")
        self.pause_requested.emit(self._is_paused)
    
    def _on_clear_clicked(self):
        self.clear_requested.emit()
    
    def set_data_count(self, count: int):
        """更新数据点数显示"""
        self._count_label.setText(f"数据点数: {count}")


class ControlPanel(QWidget):
    """主控制面板（左侧栏）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 串口配置
        self.serial_panel = SerialConfigPanel()
        layout.addWidget(self.serial_panel)
        
        # 设定值控制
        self.setpoint_panel = SetpointPanel()
        layout.addWidget(self.setpoint_panel)
        
        # PID控制
        self.pid_panel = PIDControlPanel()
        layout.addWidget(self.pid_panel)
        
        # 性能指标
        self.metrics_panel = MetricsPanel()
        layout.addWidget(self.metrics_panel)
        
        # 数据控制
        self.data_panel = DataControlPanel()
        layout.addWidget(self.data_panel)
        
        # 弹簧
        layout.addStretch()
