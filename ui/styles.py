"""
样式表和主题定义
"""

DARK_THEME = """
QMainWindow {
    background-color: #1E1E1E;
}

QWidget {
    color: #CCCCCC;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #3D3D3D;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #252526;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #CCCCCC;
}

QPushButton {
    background-color: #0E639C;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #1177BB;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton:disabled {
    background-color: #3D3D3D;
    color: #888888;
}

QComboBox {
    background-color: #3C3C3C;
    color: #FFFFFF;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px;
}

QComboBox:hover {
    border-color: #0078D4;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2D2D30;
    color: #FFFFFF;
    selection-background-color: #0078D4;
}

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

QDial {
    background-color: #3C3C3C;
}

QSpinBox, QDoubleSpinBox {
    background-color: #3C3C3C;
    color: #FFFFFF;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 2px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #0078D4;
}

QCheckBox {
    color: #CCCCCC;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #3C3C3C;
}

QCheckBox::indicator:checked {
    background-color: #0078D4;
    border-color: #0078D4;
}

QStatusBar {
    background-color: #007ACC;
    color: white;
}

QMenuBar {
    background-color: #2D2D30;
    color: #CCCCCC;
}

QMenuBar::item:selected {
    background-color: #3D3D3D;
}

QMenu {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #3D3D3D;
}

QMenu::item:selected {
    background-color: #0078D4;
}

QScrollBar:vertical {
    border: none;
    background: #2D2D30;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QSplitter::handle {
    background-color: #3D3D3D;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QToolTip {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #555555;
    padding: 4px;
}
"""
