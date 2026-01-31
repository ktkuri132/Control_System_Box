"""
滤波控制面板
支持滤波器选择、强度调节、谐波分析
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QSlider, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
import numpy as np

from core.signal_filter import (
    FilterType, SignalFilter, HarmonicAnalyzer,
    get_filter, set_all_filters_enabled, set_all_filters_type,
    set_all_filters_strength, reset_all_filters
)


class FilterControlPanel(QWidget):
    """滤波控制面板"""

    filter_changed = pyqtSignal()  # 滤波设置变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ========== 滤波设置 ==========
        filter_group = QGroupBox("信号滤波")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #4FC3F7;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        filter_layout = QVBoxLayout(filter_group)

        # 启用滤波
        self._enable_check = QCheckBox("启用滤波")
        self._enable_check.setStyleSheet("color: #FFFFFF;")
        self._enable_check.stateChanged.connect(self._on_enable_changed)
        filter_layout.addWidget(self._enable_check)

        # 滤波算法选择
        algo_layout = QHBoxLayout()
        algo_label = QLabel("算法:")
        algo_label.setStyleSheet("color: #AAAAAA;")
        algo_layout.addWidget(algo_label)

        self._algo_combo = QComboBox()
        self._algo_combo.addItems([
            FilterType.MOVING_AVERAGE,
            FilterType.EXPONENTIAL,
            FilterType.LOWPASS,
            FilterType.MEDIAN,
            FilterType.KALMAN,
            FilterType.FUSION
        ])
        self._algo_combo.setStyleSheet("""
            QComboBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        self._algo_combo.currentTextChanged.connect(self._on_algo_changed)
        algo_layout.addWidget(self._algo_combo, stretch=1)
        filter_layout.addLayout(algo_layout)

        # 滤波强度
        strength_layout = QHBoxLayout()
        strength_label = QLabel("强度:")
        strength_label.setStyleSheet("color: #AAAAAA;")
        strength_layout.addWidget(strength_label)

        self._strength_slider = QSlider(Qt.Orientation.Horizontal)
        self._strength_slider.setRange(1, 10)
        self._strength_slider.setValue(5)
        self._strength_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #3C3C3C;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -5px 0;
                background: #0078D4;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #0078D4;
                border-radius: 3px;
            }
        """)
        self._strength_slider.valueChanged.connect(self._on_strength_changed)
        strength_layout.addWidget(self._strength_slider, stretch=1)

        self._strength_value = QLabel("5")
        self._strength_value.setStyleSheet("color: #4FC3F7; min-width: 20px;")
        strength_layout.addWidget(self._strength_value)
        filter_layout.addLayout(strength_layout)

        # 算法说明
        self._algo_desc = QLabel("移动平均: 平滑噪声，响应较慢")
        self._algo_desc.setStyleSheet("color: #888888; font-size: 10px;")
        self._algo_desc.setWordWrap(True)
        filter_layout.addWidget(self._algo_desc)

        layout.addWidget(filter_group)

        # ========== 谐波分析 ==========
        harmonic_group = QGroupBox("谐波分析")
        harmonic_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #81C784;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        harmonic_layout = QVBoxLayout(harmonic_group)

        # THD 显示
        thd_layout = QHBoxLayout()
        thd_label = QLabel("总谐波失真(THD):")
        thd_label.setStyleSheet("color: #AAAAAA;")
        thd_layout.addWidget(thd_label)

        self._thd_value = QLabel("--")
        self._thd_value.setStyleSheet("color: #FF9800; font-weight: bold;")
        thd_layout.addWidget(self._thd_value)
        thd_layout.addStretch()
        harmonic_layout.addLayout(thd_layout)

        # 基频显示
        fund_layout = QHBoxLayout()
        fund_label = QLabel("基频:")
        fund_label.setStyleSheet("color: #AAAAAA;")
        fund_layout.addWidget(fund_label)

        self._fund_value = QLabel("--")
        self._fund_value.setStyleSheet("color: #4FC3F7;")
        fund_layout.addWidget(self._fund_value)
        fund_layout.addStretch()
        harmonic_layout.addLayout(fund_layout)

        # 谐波列表
        self._harmonic_table = QTableWidget()
        self._harmonic_table.setColumnCount(4)
        self._harmonic_table.setHorizontalHeaderLabels(["次数", "频率", "幅值", "相位"])
        self._harmonic_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._harmonic_table.setMaximumHeight(120)
        self._harmonic_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #3D3D3D;
                gridline-color: #3D3D3D;
            }
            QHeaderView::section {
                background-color: #3C3C3C;
                color: #FFFFFF;
                padding: 4px;
                border: none;
            }
        """)
        harmonic_layout.addWidget(self._harmonic_table)

        layout.addWidget(harmonic_group)

        # 初始状态
        self._update_algo_description()
        self._set_controls_enabled(False)

    def _set_controls_enabled(self, enabled: bool):
        """设置控件启用状态"""
        self._algo_combo.setEnabled(enabled)
        self._strength_slider.setEnabled(enabled)

    def _on_enable_changed(self, state):
        """启用/禁用滤波"""
        enabled = state == Qt.CheckState.Checked.value
        self._set_controls_enabled(enabled)
        set_all_filters_enabled(enabled)
        self.filter_changed.emit()

    def _on_algo_changed(self, algo: str):
        """滤波算法变化"""
        set_all_filters_type(algo)
        self._update_algo_description()
        self.filter_changed.emit()

    def _on_strength_changed(self, value: int):
        """滤波强度变化"""
        self._strength_value.setText(str(value))
        set_all_filters_strength(value)
        self.filter_changed.emit()

    def _update_algo_description(self):
        """更新算法说明"""
        algo = self._algo_combo.currentText()
        descriptions = {
            FilterType.MOVING_AVERAGE: "移动平均: 平滑噪声，响应较慢，适合低频信号",
            FilterType.EXPONENTIAL: "指数平滑: 响应快，平滑效果适中",
            FilterType.LOWPASS: "低通滤波: 滤除高频噪声，保留低频趋势",
            FilterType.MEDIAN: "中值滤波: 去除脉冲噪声，保留边缘",
            FilterType.KALMAN: "卡尔曼滤波: 自适应滤波，适合动态系统",
            FilterType.FUSION: "融合滤波: 结合多种算法，综合性能最佳"
        }
        self._algo_desc.setText(descriptions.get(algo, ""))

    def update_harmonic_analysis(self, analysis: dict):
        """更新谐波分析结果"""
        if not analysis or 'thd' not in analysis:
            return

        # 更新 THD
        thd = analysis.get('thd', 0)
        self._thd_value.setText(f"{thd:.2f}%")

        # THD 颜色指示
        if thd < 5:
            self._thd_value.setStyleSheet("color: #4CAF50; font-weight: bold;")  # 绿色-良好
        elif thd < 10:
            self._thd_value.setStyleSheet("color: #FF9800; font-weight: bold;")  # 橙色-一般
        else:
            self._thd_value.setStyleSheet("color: #F44336; font-weight: bold;")  # 红色-差

        # 更新基频
        fund_freq = analysis.get('fundamental_freq', 0)
        fund_mag = analysis.get('fundamental_mag', 0)
        self._fund_value.setText(f"{fund_freq:.2f} Hz (幅值: {fund_mag:.4f})")

        # 更新谐波表
        harmonics = analysis.get('harmonics', [])
        self._harmonic_table.setRowCount(min(len(harmonics), 5))

        for i, h in enumerate(harmonics[:5]):
            self._harmonic_table.setItem(i, 0, QTableWidgetItem(f"{h['order']}次"))
            self._harmonic_table.setItem(i, 1, QTableWidgetItem(f"{h['frequency']:.2f} Hz"))
            self._harmonic_table.setItem(i, 2, QTableWidgetItem(f"{h['magnitude']:.4f}"))
            self._harmonic_table.setItem(i, 3, QTableWidgetItem(f"{h['phase']:.1f}°"))

    def is_filter_enabled(self) -> bool:
        """返回滤波是否启用"""
        return self._enable_check.isChecked()

    def get_filter_type(self) -> str:
        """返回当前滤波类型"""
        return self._algo_combo.currentText()

    def get_filter_strength(self) -> int:
        """返回滤波强度"""
        return self._strength_slider.value()


class HarmonicPlotWidget(QWidget):
    """谐波分解绑图组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._analyzer = HarmonicAnalyzer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建绑图
        self._plot = pg.PlotWidget()
        self._plot.setBackground('#1E1E1E')
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel('left', '幅值')
        self._plot.setLabel('bottom', '谐波次数')

        # 柱状图
        self._bar_item = pg.BarGraphItem(x=[], height=[], width=0.6, brush='#4FC3F7')
        self._plot.addItem(self._bar_item)

        layout.addWidget(self._plot)

    def update_harmonics(self, analysis: dict):
        """更新谐波柱状图"""
        harmonics = analysis.get('harmonics', [])

        if not harmonics:
            self._bar_item.setOpts(x=[], height=[])
            return

        # 按谐波次数排序
        harmonics_sorted = sorted(harmonics, key=lambda x: x['order'])[:8]

        x = [h['order'] for h in harmonics_sorted]
        heights = [h['magnitude'] for h in harmonics_sorted]

        # 颜色根据幅值
        colors = []
        max_mag = max(heights) if heights else 1
        for h in heights:
            ratio = h / max_mag
            if ratio > 0.5:
                colors.append('#4FC3F7')  # 蓝色-主要
            elif ratio > 0.2:
                colors.append('#FF9800')  # 橙色-次要
            else:
                colors.append('#888888')  # 灰色-微弱

        self._bar_item.setOpts(x=x, height=heights, brushes=colors)
