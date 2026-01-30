"""
实时绑图组件
使用 PyQtGraph 实现高性能实时绑图
"""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMenu, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction


# 配置 PyQtGraph
pg.setConfigOptions(
    antialias=True,           # 抗锯齿
    useOpenGL=False,          # 禁用 OpenGL (某些系统兼容性问题)
    enableExperimental=False, # 禁用实验性功能
)


class ChinesePlotWidget(pg.PlotWidget):
    """带中文右键菜单的绘图组件"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 禁用默认右键菜单
        self.setMenuEnabled(False)
        self.getViewBox().setMenuEnabled(False)

        # 禁用Y轴的SI前缀（k, M, G等）
        self.getAxis('left').enableAutoSIPrefix(False)
        self.getAxis('bottom').enableAutoSIPrefix(False)

        # 状态标记
        self._grid_x = True
        self._grid_y = True
        self._antialias = True

    def setTitle(self, title, **kwargs):
        """设置图表标题"""
        self.plotItem.setTitle(title, **kwargs)

    def contextMenuEvent(self, event):
        """自定义右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #0078D4;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3D3D3D;
                margin: 5px 10px;
            }
        """)

        # ===== 视图操作 =====
        view_all_action = QAction("🔍 查看全部", self)
        view_all_action.triggered.connect(lambda: self.getViewBox().autoRange())
        menu.addAction(view_all_action)

        reset_action = QAction("🔄 重置视图", self)
        reset_action.triggered.connect(self._reset_view)
        menu.addAction(reset_action)

        menu.addSeparator()

        # ===== X轴子菜单 =====
        x_menu = menu.addMenu("📏 X 轴")
        x_auto = QAction("自动范围", self)
        x_auto.triggered.connect(lambda: self.getViewBox().enableAutoRange(axis='x'))
        x_menu.addAction(x_auto)
        x_manual = QAction("锁定范围", self)
        x_manual.triggered.connect(lambda: self.getViewBox().disableAutoRange(axis='x'))
        x_menu.addAction(x_manual)
        x_menu.addSeparator()
        x_invert = QAction("反转X轴", self)
        x_invert.setCheckable(True)
        x_invert.setChecked(self.getViewBox().xInverted())
        x_invert.triggered.connect(lambda checked: self.getViewBox().invertX(checked))
        x_menu.addAction(x_invert)

        # ===== Y轴子菜单 =====
        y_menu = menu.addMenu("📐 Y 轴")
        y_auto = QAction("自动范围", self)
        y_auto.triggered.connect(lambda: self.getViewBox().enableAutoRange(axis='y'))
        y_menu.addAction(y_auto)
        y_manual = QAction("锁定范围", self)
        y_manual.triggered.connect(lambda: self.getViewBox().disableAutoRange(axis='y'))
        y_menu.addAction(y_manual)
        y_menu.addSeparator()
        y_invert = QAction("反转Y轴", self)
        y_invert.setCheckable(True)
        y_invert.setChecked(self.getViewBox().yInverted())
        y_invert.triggered.connect(lambda checked: self.getViewBox().invertY(checked))
        y_menu.addAction(y_invert)

        menu.addSeparator()

        # ===== 显示选项 =====
        display_menu = menu.addMenu("📊 显示选项")

        grid_x = QAction("X轴网格", self)
        grid_x.setCheckable(True)
        grid_x.setChecked(self._grid_x)
        grid_x.triggered.connect(self._toggle_grid_x)
        display_menu.addAction(grid_x)

        grid_y = QAction("Y轴网格", self)
        grid_y.setCheckable(True)
        grid_y.setChecked(self._grid_y)
        grid_y.triggered.connect(self._toggle_grid_y)
        display_menu.addAction(grid_y)

        display_menu.addSeparator()

        antialias = QAction("抗锯齿", self)
        antialias.setCheckable(True)
        antialias.setChecked(self._antialias)
        antialias.triggered.connect(self._toggle_antialias)
        display_menu.addAction(antialias)

        # ===== 鼠标模式 =====
        mouse_menu = menu.addMenu("🖱️ 鼠标模式")
        pan_mode = QAction("平移模式", self)
        pan_mode.triggered.connect(lambda: self.getViewBox().setMouseMode(pg.ViewBox.PanMode))
        mouse_menu.addAction(pan_mode)
        rect_mode = QAction("框选缩放", self)
        rect_mode.triggered.connect(lambda: self.getViewBox().setMouseMode(pg.ViewBox.RectMode))
        mouse_menu.addAction(rect_mode)

        menu.addSeparator()

        # ===== 导出功能 =====
        export_menu = menu.addMenu("💾 导出")

        export_png = QAction("导出为 PNG 图片", self)
        export_png.triggered.connect(lambda: self._export_image('png'))
        export_menu.addAction(export_png)

        export_jpg = QAction("导出为 JPG 图片", self)
        export_jpg.triggered.connect(lambda: self._export_image('jpg'))
        export_menu.addAction(export_jpg)

        export_svg = QAction("导出为 SVG 矢量图", self)
        export_svg.triggered.connect(lambda: self._export_image('svg'))
        export_menu.addAction(export_svg)

        export_menu.addSeparator()

        copy_action = QAction("复制到剪贴板", self)
        copy_action.triggered.connect(self._copy_to_clipboard)
        export_menu.addAction(copy_action)

        menu.exec(event.globalPos())

    def _reset_view(self):
        """重置视图"""
        self.getViewBox().autoRange()
        self.getViewBox().enableAutoRange()

    def _toggle_grid_x(self, checked):
        """切换X轴网格"""
        self._grid_x = checked
        self.showGrid(x=self._grid_x, y=self._grid_y)

    def _toggle_grid_y(self, checked):
        """切换Y轴网格"""
        self._grid_y = checked
        self.showGrid(x=self._grid_x, y=self._grid_y)

    def _toggle_antialias(self, checked):
        """切换抗锯齿"""
        self._antialias = checked
        pg.setConfigOption('antialias', checked)

    def _export_image(self, fmt):
        """导出图片"""
        ext_map = {'png': 'PNG图片 (*.png)', 'jpg': 'JPG图片 (*.jpg)', 'svg': 'SVG矢量图 (*.svg)'}
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出图表", f"chart.{fmt}", ext_map.get(fmt, f'{fmt.upper()}文件 (*.{fmt})')
        )
        if file_path:
            try:
                from pyqtgraph.exporters import ImageExporter, SVGExporter
                if fmt == 'svg':
                    exporter = SVGExporter(self.plotItem)
                else:
                    exporter = ImageExporter(self.plotItem)
                exporter.export(file_path)
            except Exception as e:
                print(f"导出失败: {e}")

    def _copy_to_clipboard(self):
        """复制图表到剪贴板"""
        try:
            from pyqtgraph.exporters import ImageExporter
            exporter = ImageExporter(self.plotItem)
            exporter.export(copy=True)
        except Exception as e:
            print(f"复制失败: {e}")



class RealtimePlotWidget(QWidget):
    """实时绘图组件"""
    
    # 预定义颜色方案
    COLORS = {
        'setpoint': '#FF6B6B',      # 红色 - 设定值
        'process_value': '#4ECDC4', # 青色 - 过程值
        'error': '#FFE66D',         # 黄色 - 误差
        'output': '#95E1D3',        # 绿色 - 控制输出
        'fft': '#DDA0DD',           # 紫色 - FFT
        'grid': '#404040',          # 深灰 - 网格
        'background': '#1E1E1E',    # 深色背景
    }
    
    def __init__(self, title: str = "实时曲线", parent=None):
        super().__init__(parent)
        self._title = title
        self._max_points = 1000  # 默认显示最近1000个点
        self._auto_scale = True
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF; padding: 2px;")
        title_layout.addWidget(title_label)

        # ★ 实时数值显示标签
        self._value_label = QLabel("")
        self._value_label.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                background-color: #1E1E1E;
                border: 1px solid #3C3C3C;
                border-radius: 3px;
                padding: 2px 8px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self._value_label.setMinimumWidth(300)
        title_layout.addWidget(self._value_label)

        title_layout.addStretch()
        
        # 自动缩放按钮
        self._auto_scale_btn = QPushButton("🔄 自动缩放")
        self._auto_scale_btn.setCheckable(True)
        self._auto_scale_btn.setChecked(True)
        self._auto_scale_btn.clicked.connect(self._on_auto_scale_clicked)
        self._auto_scale_btn.setFixedWidth(90)
        self._auto_scale_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:checked {
                background-color: #388E3C;
            }
            QPushButton:!checked {
                background-color: #555555;
            }
        """)
        title_layout.addWidget(self._auto_scale_btn)
        
        # 显示点数选择
        points_label = QLabel("显示点数:")
        points_label.setStyleSheet("color: #AAAAAA;")
        self._points_combo = QComboBox()
        self._points_combo.addItems(["500", "1000", "2000", "5000", "全部"])
        self._points_combo.setCurrentIndex(1)
        self._points_combo.currentTextChanged.connect(self._on_points_changed)
        self._points_combo.setFixedWidth(80)
        
        title_layout.addWidget(points_label)
        title_layout.addWidget(self._points_combo)
        
        layout.addLayout(title_layout)
        
        # 创建绑图窗口（使用自定义中文菜单）
        self._plot_widget = ChinesePlotWidget()
        self._plot_widget.setBackground(self.COLORS['background'])
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.setLabel('bottom', '时间', units='秒')
        
        # 添加图例
        self._plot_widget.addLegend(offset=(10, 10))
        
        # 监听手动缩放事件
        self._plot_widget.sigRangeChanged.connect(self._on_range_changed)
        
        layout.addWidget(self._plot_widget)
        
        # 初始化曲线
        self._curves = {}
        self._latest_values = {}  # 存储每条曲线的最新值
        self._is_updating = False  # 防止更新数据时触发range changed
    
    def _on_auto_scale_clicked(self, checked: bool):
        """自动缩放按钮点击"""
        self._auto_scale = checked
        if checked:
            self._plot_widget.enableAutoRange()
            self._auto_scale_btn.setText("🔄 自动缩放")
        else:
            self._plot_widget.disableAutoRange()
            self._auto_scale_btn.setText("📌 已锁定")
    
    def _on_range_changed(self, view_box, ranges):
        """当用户手动缩放/平移时，禁用自动缩放"""
        # 如果正在程序更新数据，忽略这个事件
        if self._is_updating:
            return
        
        # 用户手动操作了，关闭自动缩放
        if self._auto_scale:
            self._auto_scale = False
            self._auto_scale_btn.setChecked(False)
            self._auto_scale_btn.setText("📌 已锁定")
    
    def _on_points_changed(self, text: str):
        """显示点数改变"""
        if text == "全部":
            self._max_points = None
        else:
            self._max_points = int(text)
    
    def add_curve(self, name: str, color: str = None, width: int = 2) -> pg.PlotDataItem:
        """添加一条曲线"""
        if color is None:
            color = self.COLORS.get(name, '#FFFFFF')
        
        pen = pg.mkPen(color=color, width=width)
        curve = self._plot_widget.plot([], [], pen=pen, name=name)
        self._curves[name] = curve
        return curve
    
    def update_curve(self, name: str, x: np.ndarray, y: np.ndarray):
        """更新曲线数据"""
        if name not in self._curves:
            self.add_curve(name)
        
        # 确保是numpy数组并复制数据
        x = np.asarray(x).copy()
        y = np.asarray(y).copy()

        # 限制显示点数
        if self._max_points and len(x) > self._max_points:
            x = x[-self._max_points:]
            y = y[-self._max_points:]
        
        # 设置标志，防止数据更新触发range changed
        self._is_updating = True
        self._curves[name].setData(x, y)
        self._is_updating = False

        # 更新最新值显示 - 使用 .item() 确保获取Python原生类型
        if len(y) > 0:
            self._latest_values[name] = y[-1].item() if hasattr(y[-1], 'item') else float(y[-1])
            self._update_value_display()

    def _update_value_display(self):
        """更新实时数值显示"""
        if not self._latest_values:
            return

        parts = []
        for name, latest_val in self._latest_values.items():
            # 格式化数值，避免科学计数法
            abs_val = abs(latest_val)
            if abs_val >= 1000:
                val_str = f"{latest_val:.1f}"
            elif abs_val >= 1:
                val_str = f"{latest_val:.3f}"
            elif abs_val >= 0.001:
                val_str = f"{latest_val:.4f}"
            elif abs_val == 0:
                val_str = "0"
            else:
                val_str = f"{latest_val:.6f}"
            parts.append(f"{name}: {val_str}")

        if parts:
            self._value_label.setText("  |  ".join(parts))

    def clear_curves(self):
        """清空所有曲线数据"""
        self._is_updating = True
        for curve in self._curves.values():
            curve.setData([], [])
        self._is_updating = False
        self._latest_values.clear()
        self._value_label.setText("")

    def set_y_label(self, label: str, units: str = None):
        """设置Y轴标签"""
        self._plot_widget.setLabel('left', label, units=units)
    
    def set_x_range(self, min_val: float, max_val: float):
        """设置X轴范围"""
        self._plot_widget.setXRange(min_val, max_val, padding=0)
    
    def set_y_range(self, min_val: float, max_val: float):
        """设置Y轴范围"""
        self._plot_widget.setYRange(min_val, max_val, padding=0.05)
    
    def enable_auto_range(self, enable: bool = True):
        """启用/禁用自动缩放"""
        self._auto_scale = enable
        self._plot_widget.enableAutoRange(enable)


class ResponsePlotWidget(RealtimePlotWidget):
    """系统响应曲线图（SP, PV, Error）"""
    
    def __init__(self, parent=None):
        super().__init__("系统响应曲线", parent)
        self.set_y_label("数值")
        
        # 添加预定义曲线
        self.add_curve('setpoint', self.COLORS['setpoint'], width=2)
        self.add_curve('process_value', self.COLORS['process_value'], width=2)
        self.add_curve('error', self.COLORS['error'], width=1)
    
    def update_data(self, timestamps: np.ndarray, setpoints: np.ndarray, 
                    process_values: np.ndarray, errors: np.ndarray):
        """更新响应数据"""
        self.update_curve('setpoint', timestamps, setpoints)
        self.update_curve('process_value', timestamps, process_values)
        self.update_curve('error', timestamps, errors)


class OutputPlotWidget(RealtimePlotWidget):
    """控制输出曲线图"""
    
    def __init__(self, parent=None):
        super().__init__("控制输出", parent)
        self.set_y_label("输出值")
        self.add_curve('output', self.COLORS['output'], width=2)
    
    def update_data(self, timestamps: np.ndarray, outputs: np.ndarray):
        """更新输出数据"""
        self.update_curve('output', timestamps, outputs)


class FFTPlotWidget(RealtimePlotWidget):
    """频谱分析图"""
    
    def __init__(self, parent=None):
        super().__init__("频谱分析 (FFT)", parent)
        self._plot_widget.setLabel('bottom', '频率', units='Hz')
        self.set_y_label("幅值")
        self.add_curve('fft', self.COLORS['fft'], width=2)
        
        # FFT 图通常使用对数坐标
        self._plot_widget.setLogMode(x=False, y=False)
    
    def update_data(self, frequencies: np.ndarray, magnitudes: np.ndarray):
        """更新FFT数据"""
        if len(frequencies) > 0:
            self.update_curve('fft', frequencies, magnitudes)


class MultiPlotWidget(QWidget):
    """多图组合组件 - 串口模式使用，与仿真模式功能同步"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._analysis_window = None
        self._extended_window = None
        self._cached_data = {}
        self._setup_ui()
    
    def _setup_ui(self):
        from PyQt6.QtWidgets import QMainWindow
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 系统响应图（主图）
        self.response_plot = RealtimePlotWidget("系统响应曲线 (设定值 vs 过程值)")
        self.response_plot.set_y_label("数值")
        self.response_plot.add_curve('设定值', '#FF6B6B', width=2)
        self.response_plot.add_curve('过程值', '#4ECDC4', width=2)
        layout.addWidget(self.response_plot, stretch=1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 打开详细分析窗口按钮
        self._analysis_btn = QPushButton("📈 详细分析 (误差/输出/FFT)")
        self._analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
        """)
        self._analysis_btn.clicked.connect(self._open_analysis_window)
        btn_layout.addWidget(self._analysis_btn)
        
        # 打开扩展分析窗口按钮
        self._extended_btn = QPushButton("📊 扩展分析 (性能指标/稳定性/波特图)")
        self._extended_btn.setStyleSheet("""
            QPushButton {
                background-color: #6A4C93;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7D5BA6;
            }
        """)
        self._extended_btn.clicked.connect(self._open_extended_window)
        btn_layout.addWidget(self._extended_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 保留 fft_plot 供 main_window 调用（内部不显示，只在分析窗口显示）
        self.fft_plot = FFTPlotWidget()
        self.fft_plot.setVisible(False)
        layout.addWidget(self.fft_plot)
    
    def _open_analysis_window(self):
        """打开详细分析窗口"""
        from ui.simulator_plot_widgets import AnalysisWindow
        if self._analysis_window is None or not self._analysis_window.isVisible():
            self._analysis_window = AnalysisWindow(self)
            if self._cached_data:
                self._analysis_window.update_data(**self._cached_data)
        self._analysis_window.show()
        self._analysis_window.raise_()
        self._analysis_window.activateWindow()
    
    def _open_extended_window(self):
        """打开扩展分析窗口"""
        from ui.simulator_plot_widgets import ExtendedAnalysisWindow
        if self._extended_window is None or not self._extended_window.isVisible():
            self._extended_window = ExtendedAnalysisWindow(self)
            if self._cached_data:
                self._extended_window.update_data(**self._cached_data)
        self._extended_window.show()
        self._extended_window.raise_()
        self._extended_window.activateWindow()
    
    def update_all(self, timestamps: np.ndarray, setpoints: np.ndarray,
                   process_values: np.ndarray, outputs: np.ndarray,
                   errors: np.ndarray, fft_freq: np.ndarray = None,
                   fft_mag: np.ndarray = None):
        """更新所有图表"""
        if len(timestamps) == 0:
            return
        
        # 缓存数据供分析窗口使用
        self._cached_data = {
            'timestamps': timestamps,
            'setpoints': setpoints,
            'process_values': process_values,
            'errors': errors,
            'outputs': outputs
        }
        
        # 更新主响应曲线
        self.response_plot.update_curve('设定值', timestamps, setpoints)
        self.response_plot.update_curve('过程值', timestamps, process_values)

        # 更新FFT（用于分析窗口）
        if fft_freq is not None and fft_mag is not None:
            self.fft_plot.update_data(fft_freq, fft_mag)
        
        # 更新详细分析窗口（如果打开）
        if self._analysis_window and self._analysis_window.isVisible():
            self._analysis_window.update_data(**self._cached_data)
            if fft_freq is not None and fft_mag is not None:
                self._analysis_window.update_fft(fft_freq, fft_mag)
        
        # 更新扩展分析窗口（如果打开）
        if self._extended_window and self._extended_window.isVisible():
            self._extended_window.update_data(**self._cached_data)
    
    def update_fft(self, frequencies: np.ndarray, magnitudes: np.ndarray):
        """更新FFT数据（供分析窗口使用）"""
        self.fft_plot.update_data(frequencies, magnitudes)
        if self._analysis_window and self._analysis_window.isVisible():
            self._analysis_window.update_fft(frequencies, magnitudes)
    
    def clear_all(self):
        """清空所有图表"""
        self.response_plot.clear_curves()
        self.fft_plot.clear_curves()
        if self._analysis_window:
            self._analysis_window.clear_all()
        if self._extended_window:
            self._extended_window.clear_all()
        self._cached_data = {}
