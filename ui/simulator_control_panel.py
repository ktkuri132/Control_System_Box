"""
仿真数据接收配置面板
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QLineEdit, QSpinBox,
    QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator

from ui.control_panel import StyledGroupBox


class SimulatorConfigPanel(StyledGroupBox):
    """仿真数据接收配置面板"""
    connect_requested = pyqtSignal(str, int)  # (host, port)
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
        """设置连接状态"""
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
    
    def set_system_type(self, system_type: str):
        """设置系统类型显示"""
        type_names = {
            'inverted_pendulum': '倒立摆系统',
            'ball_on_plate': '滚球控制系统',
        }
        name = type_names.get(system_type, system_type)
        self._system_label.setText(f"系统类型: {name}")


class SimulatorMetricsPanel(StyledGroupBox):
    """仿真系统性能指标面板"""
    
    def __init__(self, parent=None):
        super().__init__("仿真性能指标", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(5)
        
        # 创建指标显示标签
        self._metrics = {}
        
        # 倒立摆指标
        pendulum_metrics = [
            ("angle", "当前角度", "°"),
            ("cart_pos", "小车位置", "m"),
            ("force", "控制力", "N"),
            ("max_angle", "最大偏角", "°"),
        ]
        
        # 滚球系统指标
        ball_metrics = [
            ("error", "位置误差", "mm"),
            ("ball_pos", "小球位置", "mm"),
            ("plate_angle", "平板角度", "°"),
            ("max_error", "最大误差", "mm"),
        ]
        
        # 合并所有指标
        all_metrics = pendulum_metrics + ball_metrics
        
        for i, (key, name, unit) in enumerate(all_metrics):
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
    
    def update_pendulum_metrics(self, angle: float, cart_pos: float, 
                                 force: float, max_angle: float):
        """更新倒立摆指标"""
        self._metrics["angle"].setText(f"{angle:.2f}")
        self._metrics["cart_pos"].setText(f"{cart_pos:.3f}")
        self._metrics["force"].setText(f"{force:.1f}")
        self._metrics["max_angle"].setText(f"{max_angle:.2f}")
    
    def update_ball_metrics(self, error: float, ball_x: float, ball_y: float,
                            plate_x: float, plate_y: float, max_error: float):
        """更新滚球系统指标"""
        self._metrics["error"].setText(f"{error:.1f}")
        self._metrics["ball_pos"].setText(f"({ball_x:.1f}, {ball_y:.1f})")
        self._metrics["plate_angle"].setText(f"({plate_x:.1f}, {plate_y:.1f})")
        self._metrics["max_error"].setText(f"{max_error:.1f}")
    
    def clear(self):
        """清空所有指标"""
        for label in self._metrics.values():
            label.setText("--")


class SimulatorControlPanel(QWidget):
    """仿真模式控制面板（左侧栏）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # UDP配置面板
        self.config_panel = SimulatorConfigPanel()
        layout.addWidget(self.config_panel)
        
        # 性能指标面板
        self.metrics_panel = SimulatorMetricsPanel()
        layout.addWidget(self.metrics_panel)
        
        # 数据控制面板（复用）
        from ui.control_panel import DataControlPanel
        self.data_panel = DataControlPanel()
        layout.addWidget(self.data_panel)
        
        # 弹簧
        layout.addStretch()
