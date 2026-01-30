"""
仿真数据专用绘图组件
针对倒立摆和滚球控制系统的特化图表
增加标准响应控制曲线
"""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QTabWidget, QSplitter, QPushButton, QMainWindow, QGridLayout,
    QGroupBox, QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.plot_widgets import RealtimePlotWidget, ResponsePlotWidget, OutputPlotWidget, FFTPlotWidget, ChinesePlotWidget


class MetricCard(QFrame):
    """性能指标卡片"""
    
    def __init__(self, title: str, unit: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            MetricCard {
                background-color: #2D2D2D;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
            }
        """)
        self.setFixedHeight(85)
        self.setMinimumWidth(140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        
        # 标题
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("color: #888888; font-size: 11px; background: transparent; border: none;")
        self._title_label.setFixedHeight(16)
        layout.addWidget(self._title_label)
        
        # 数值
        self._value_label = QLabel("--")
        self._value_label.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        self._value_label.setFixedHeight(24)
        layout.addWidget(self._value_label)
        
        # 单位/状态
        self._status_label = QLabel(self._unit)
        self._status_label.setStyleSheet("color: #666666; font-size: 10px; background: transparent; border: none;")
        self._status_label.setFixedHeight(14)
        layout.addWidget(self._status_label)
    
    def set_value(self, value, status_color: str = None, status_text: str = None):
        """设置数值"""
        # 检查是否为数值类型（包括 numpy 类型）
        try:
            float_val = float(value)
            if abs(float_val) < 0.01 and float_val != 0:
                self._value_label.setText(f"{float_val:.4f}")
            elif abs(float_val) < 1:
                self._value_label.setText(f"{float_val:.3f}")
            else:
                self._value_label.setText(f"{float_val:.2f}")
        except (TypeError, ValueError):
            self._value_label.setText(str(value))
        
        if status_color:
            self._value_label.setStyleSheet(f"color: {status_color}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        
        if status_text:
            self._status_label.setText(f"{self._unit} ({status_text})")
    
    def clear(self):
        """清空数值"""
        self._value_label.setText("--")
        self._value_label.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        self._status_label.setText(self._unit)


class StabilityGauge(QWidget):
    """稳定性评估仪表盘"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("🎯 系统稳定性评估")
        title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 评分
        self._score_label = QLabel("--")
        self._score_label.setStyleSheet("color: #4ECDC4; font-size: 48px; font-weight: bold;")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._score_label)
        
        # 进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet("""
            QProgressBar {
                background-color: #3C3C3C;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4ECDC4;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._progress)
        
        # 状态文字
        self._status_label = QLabel("等待数据...")
        self._status_label.setStyleSheet("color: #888888; font-size: 12px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        
        layout.addStretch()
    
    def set_score(self, score: float, status: str):
        """设置稳定性评分 (0-100)"""
        score = max(0, min(100, score))
        self._score_label.setText(f"{score:.0f}")
        self._progress.setValue(int(score))
        self._status_label.setText(status)
        
        # 根据分数设置颜色
        if score >= 80:
            color = "#4ECDC4"  # 绿色 - 优秀
        elif score >= 60:
            color = "#FFE66D"  # 黄色 - 良好
        elif score >= 40:
            color = "#FF9800"  # 橙色 - 一般
        else:
            color = "#FF6B6B"  # 红色 - 差
        
        self._score_label.setStyleSheet(f"color: {color}; font-size: 48px; font-weight: bold;")
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #3C3C3C;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
    
    def clear(self):
        """清空"""
        self._score_label.setText("--")
        self._progress.setValue(0)
        self._status_label.setText("等待数据...")


class ExtendedAnalysisWindow(QMainWindow):
    """扩展分析窗口 - 包含性能指标、稳定性评估、波特图等"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 扩展分析窗口 - 控制系统性能分析")
        self.setMinimumSize(1200, 900)
        self.resize(1400, 1000)
        self._cached_data = {}
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
            }
            QGroupBox {
                background-color: #252526;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #FFFFFF;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("📈 控制系统扩展性能分析")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        header.addWidget(title)
        header.addStretch()
        
        # 刷新按钮
        self._refresh_btn = QPushButton("🔄 刷新分析")
        self._refresh_btn.setStyleSheet("""
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
        self._refresh_btn.clicked.connect(self._refresh_analysis)
        header.addWidget(self._refresh_btn)
        
        main_layout.addLayout(header)
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：指标面板（使用滚动区域）
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # ========== 稳定性评估 ==========
        stability_group = QGroupBox("🎯 系统稳定性评估")
        stability_layout = QVBoxLayout(stability_group)
        self._stability_gauge = StabilityGauge()
        stability_layout.addWidget(self._stability_gauge)
        left_layout.addWidget(stability_group)
        
        # ========== 时域性能指标（经典控制） ==========
        time_group = QGroupBox("⏱️ 时域性能指标 (经典控制)")
        time_layout = QGridLayout(time_group)
        time_layout.setSpacing(6)
        
        # 基本时域指标
        self._rise_time_card = MetricCard("上升时间 (Tr)", "秒")
        self._settling_time_card = MetricCard("调节时间 (Ts)", "秒")
        self._overshoot_card = MetricCard("超调量 (Mp)", "%")
        self._peak_time_card = MetricCard("峰值时间 (Tp)", "秒")
        self._delay_time_card = MetricCard("延迟时间 (Td)", "秒")
        self._steady_error_card = MetricCard("稳态误差 (Ess)", "")
        
        time_layout.addWidget(self._rise_time_card, 0, 0)
        time_layout.addWidget(self._settling_time_card, 0, 1)
        time_layout.addWidget(self._overshoot_card, 1, 0)
        time_layout.addWidget(self._peak_time_card, 1, 1)
        time_layout.addWidget(self._delay_time_card, 2, 0)
        time_layout.addWidget(self._steady_error_card, 2, 1)
        
        left_layout.addWidget(time_group)
        
        # ========== 动态特性指标 ==========
        dynamic_group = QGroupBox("📐 动态特性指标")
        dynamic_layout = QGridLayout(dynamic_group)
        dynamic_layout.setSpacing(6)
        
        self._oscillation_card = MetricCard("振荡次数", "次")
        self._damping_ratio_card = MetricCard("阻尼比 (ζ)", "")
        self._natural_freq_card = MetricCard("自然频率 (ωn)", "rad/s")
        self._decay_ratio_card = MetricCard("衰减比", "")
        
        dynamic_layout.addWidget(self._oscillation_card, 0, 0)
        dynamic_layout.addWidget(self._damping_ratio_card, 0, 1)
        dynamic_layout.addWidget(self._natural_freq_card, 1, 0)
        dynamic_layout.addWidget(self._decay_ratio_card, 1, 1)
        
        left_layout.addWidget(dynamic_group)
        
        # ========== 频域性能指标 ==========
        freq_group = QGroupBox("📊 频域性能指标")
        freq_layout = QGridLayout(freq_group)
        freq_layout.setSpacing(6)
        
        self._bandwidth_card = MetricCard("带宽 (BW)", "Hz")
        self._resonance_card = MetricCard("谐振峰值 (Mr)", "dB")
        self._resonance_freq_card = MetricCard("谐振频率 (ωr)", "Hz")
        self._cutoff_freq_card = MetricCard("截止频率 (ωc)", "Hz")
        self._phase_margin_card = MetricCard("相位裕度 (PM)", "°")
        self._gain_margin_card = MetricCard("增益裕度 (GM)", "dB")
        
        freq_layout.addWidget(self._bandwidth_card, 0, 0)
        freq_layout.addWidget(self._resonance_card, 0, 1)
        freq_layout.addWidget(self._resonance_freq_card, 1, 0)
        freq_layout.addWidget(self._cutoff_freq_card, 1, 1)
        freq_layout.addWidget(self._phase_margin_card, 2, 0)
        freq_layout.addWidget(self._gain_margin_card, 2, 1)
        
        left_layout.addWidget(freq_group)
        
        # ========== 现代控制/统计指标 ==========
        modern_group = QGroupBox("📉 统计与质量指标")
        modern_layout = QGridLayout(modern_group)
        modern_layout.setSpacing(6)
        
        self._iae_card = MetricCard("IAE", "积分绝对误差")
        self._ise_card = MetricCard("ISE", "积分平方误差")
        self._itae_card = MetricCard("ITAE", "时间加权IAE")
        self._rmse_card = MetricCard("RMSE", "均方根误差")
        self._mae_card = MetricCard("MAE", "平均绝对误差")
        self._std_error_card = MetricCard("误差标准差", "σ")
        
        modern_layout.addWidget(self._iae_card, 0, 0)
        modern_layout.addWidget(self._ise_card, 0, 1)
        modern_layout.addWidget(self._itae_card, 1, 0)
        modern_layout.addWidget(self._rmse_card, 1, 1)
        modern_layout.addWidget(self._mae_card, 2, 0)
        modern_layout.addWidget(self._std_error_card, 2, 1)
        
        left_layout.addWidget(modern_group)
        
        # ========== 控制能量指标 ==========
        energy_group = QGroupBox("⚡ 控制能量指标")
        energy_layout = QGridLayout(energy_group)
        energy_layout.setSpacing(6)
        
        self._control_effort_card = MetricCard("控制能量", "∫u²dt")
        self._max_control_card = MetricCard("最大控制量", "")
        self._control_variance_card = MetricCard("控制量方差", "")
        self._smoothness_card = MetricCard("平滑度", "∫(du/dt)²")
        
        energy_layout.addWidget(self._control_effort_card, 0, 0)
        energy_layout.addWidget(self._max_control_card, 0, 1)
        energy_layout.addWidget(self._control_variance_card, 1, 0)
        energy_layout.addWidget(self._smoothness_card, 1, 1)
        
        left_layout.addWidget(energy_group)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_widget)
        splitter.addWidget(left_scroll)
        
        # 右侧：图表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 阶跃响应分析图
        self._step_response_plot = ChinesePlotWidget()
        self._step_response_plot.setTitle("阶跃响应分析")
        self._step_response_plot.setBackground('#252526')
        self._step_response_plot.showGrid(x=True, y=True, alpha=0.3)
        self._step_response_plot.setLabel('left', '幅值')
        self._step_response_plot.setLabel('bottom', '时间 (s)')
        self._step_response_plot.addLegend(offset=(10, 10))
        
        # 响应曲线
        self._response_curve = self._step_response_plot.plot([], [], pen=pg.mkPen('#4ECDC4', width=2), name='响应')
        self._setpoint_curve = self._step_response_plot.plot([], [], pen=pg.mkPen('#FF6B6B', width=2, style=Qt.PenStyle.DashLine), name='设定值')
        # 性能指标标注线
        self._rise_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#FFE66D', width=1, style=Qt.PenStyle.DotLine))
        self._settling_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#95E1D3', width=1, style=Qt.PenStyle.DotLine))
        self._peak_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#DDA0DD', width=1, style=Qt.PenStyle.DotLine))
        self._overshoot_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('#FF9800', width=1, style=Qt.PenStyle.DotLine))
        self._step_response_plot.addItem(self._rise_line)
        self._step_response_plot.addItem(self._settling_line)
        self._step_response_plot.addItem(self._peak_line)
        self._step_response_plot.addItem(self._overshoot_line)
        
        right_layout.addWidget(self._step_response_plot, stretch=2)
        
        # 波特图（幅频特性）
        self._bode_mag_plot = ChinesePlotWidget()
        self._bode_mag_plot.setTitle("波特图 - 幅频特性")
        self._bode_mag_plot.setBackground('#252526')
        self._bode_mag_plot.showGrid(x=True, y=True, alpha=0.3)
        self._bode_mag_plot.setLabel('left', '幅值 (dB)')
        self._bode_mag_plot.setLabel('bottom', '频率 (Hz)')
        self._bode_mag_plot.setLogMode(x=True, y=False)
        self._bode_mag_curve = self._bode_mag_plot.plot([], [], pen=pg.mkPen('#4ECDC4', width=2))
        # -3dB线
        self._bode_3db_line = pg.InfiniteLine(pos=-3, angle=0, pen=pg.mkPen('#FF6B6B', width=1, style=Qt.PenStyle.DashLine))
        self._bode_mag_plot.addItem(self._bode_3db_line)
        
        right_layout.addWidget(self._bode_mag_plot, stretch=1)
        
        # 误差分布直方图
        self._error_hist_plot = ChinesePlotWidget()
        self._error_hist_plot.setTitle("误差分布直方图")
        self._error_hist_plot.setBackground('#252526')
        self._error_hist_plot.showGrid(x=True, y=True, alpha=0.3)
        self._error_hist_plot.setLabel('left', '频次')
        self._error_hist_plot.setLabel('bottom', '误差值')
        
        right_layout.addWidget(self._error_hist_plot, stretch=1)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([420, 780])
        
        main_layout.addWidget(splitter)
    
    def update_data(self, timestamps: np.ndarray, setpoints: np.ndarray,
                    process_values: np.ndarray, errors: np.ndarray,
                    outputs: np.ndarray):
        """更新数据并分析"""
        if len(timestamps) < 10:
            return
        
        self._cached_data = {
            'timestamps': timestamps,
            'setpoints': setpoints,
            'process_values': process_values,
            'errors': errors,
            'outputs': outputs
        }
        
        self._analyze_performance()
    
    def _refresh_analysis(self):
        """刷新分析"""
        if self._cached_data:
            self._analyze_performance()
    
    def _analyze_performance(self):
        """执行性能分析"""
        if not self._cached_data:
            print("[DEBUG] _analyze_performance: 无缓存数据，返回")
            return
        
        timestamps = self._cached_data['timestamps']
        setpoints = self._cached_data['setpoints']
        process_values = self._cached_data['process_values']
        errors = self._cached_data['errors']
        outputs = self._cached_data['outputs']
        
        # 更新响应曲线
        self._response_curve.setData(timestamps, process_values)
        self._setpoint_curve.setData(timestamps, setpoints)
        
        # 计算时域性能指标
        self._calculate_time_domain_metrics(timestamps, setpoints, process_values, errors)
        
        # 计算动态特性指标
        self._calculate_dynamic_metrics(timestamps, setpoints, process_values, errors)
        
        # 计算频域性能指标
        self._calculate_frequency_domain_metrics(timestamps, errors)
        
        # 计算统计与质量指标
        self._calculate_statistical_metrics(timestamps, errors)
        
        # 计算控制能量指标
        self._calculate_control_energy_metrics(timestamps, outputs)
        
        # 更新误差直方图
        self._update_error_histogram(errors)
        
        # 计算稳定性评分
        self._calculate_stability_score(timestamps, setpoints, process_values, errors)
    
    def _calculate_time_domain_metrics(self, timestamps, setpoints, process_values, errors):
        """计算时域性能指标（经典控制）"""
        if len(timestamps) < 10:
            return
        
        # 找到阶跃变化点
        sp_diff = np.diff(setpoints)
        step_indices = np.where(np.abs(sp_diff) > np.std(sp_diff) * 2)[0]
        
        if len(step_indices) == 0:
            start_idx = 0
            final_value = setpoints[-1]
            initial_value = process_values[0]
        else:
            start_idx = step_indices[-1] + 1
            final_value = setpoints[start_idx] if start_idx < len(setpoints) else setpoints[-1]
            initial_value = process_values[start_idx] if start_idx < len(process_values) else process_values[0]
        
        t = timestamps[start_idx:] - timestamps[start_idx]
        pv = process_values[start_idx:]
        
        if len(t) < 5:
            return
        
        delta = final_value - initial_value
        if abs(delta) < 1e-6:
            delta = 1
        
        # 1. 延迟时间 (Td) - 到达50%的时间
        target_50 = initial_value + 0.5 * delta
        t_50 = None
        for i, v in enumerate(pv):
            if (delta > 0 and v >= target_50) or (delta < 0 and v <= target_50):
                t_50 = t[i]
                break
        if t_50 is not None:
            self._delay_time_card.set_value(t_50)
        else:
            self._delay_time_card.set_value("N/A")
        
        # 2. 上升时间 (Tr) - 10% -> 90%
        target_10 = initial_value + 0.1 * delta
        target_90 = initial_value + 0.9 * delta
        t_10 = None
        t_90 = None
        for i, v in enumerate(pv):
            if t_10 is None and ((delta > 0 and v >= target_10) or (delta < 0 and v <= target_10)):
                t_10 = t[i]
            if t_90 is None and ((delta > 0 and v >= target_90) or (delta < 0 and v <= target_90)):
                t_90 = t[i]
                break
        
        rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else None
        if rise_time is not None and rise_time > 0:
            self._rise_time_card.set_value(rise_time)
            self._rise_line.setPos(timestamps[start_idx] + t_90 if t_90 else 0)
        else:
            self._rise_time_card.set_value("N/A")
        
        # 3. 超调量 (Mp)
        if delta > 0:
            peak_value = np.max(pv)
            overshoot = ((peak_value - final_value) / abs(delta)) * 100
        else:
            peak_value = np.min(pv)
            overshoot = ((final_value - peak_value) / abs(delta)) * 100
        
        overshoot = max(0, overshoot)
        peak_idx = np.argmax(pv) if delta > 0 else np.argmin(pv)
        peak_time = t[peak_idx]
        
        if overshoot > 0.1:
            status = "过大" if overshoot > 25 else ("适中" if overshoot > 10 else "良好")
            color = "#FF6B6B" if overshoot > 25 else ("#FFE66D" if overshoot > 10 else "#4ECDC4")
            self._overshoot_card.set_value(overshoot, status_color=color, status_text=status)
            self._overshoot_line.setPos(peak_value)
        else:
            self._overshoot_card.set_value(0, status_color="#4ECDC4", status_text="无超调")
        
        # 4. 峰值时间 (Tp)
        self._peak_time_card.set_value(peak_time)
        self._peak_line.setPos(timestamps[start_idx] + peak_time)
        
        # 5. 调节时间 (Ts) - 进入±5%范围
        tolerance = 0.05 * abs(delta)
        settling_time = None
        for i in range(len(pv) - 1, -1, -1):
            if abs(pv[i] - final_value) > tolerance:
                settling_time = t[min(i + 1, len(t) - 1)]
                break
        
        if settling_time is not None:
            status = "较慢" if settling_time > 2 else ("适中" if settling_time > 0.5 else "快速")
            color = "#FF6B6B" if settling_time > 2 else ("#FFE66D" if settling_time > 0.5 else "#4ECDC4")
            self._settling_time_card.set_value(settling_time, status_color=color, status_text=status)
            self._settling_line.setPos(timestamps[start_idx] + settling_time)
        else:
            self._settling_time_card.set_value("未稳定", status_color="#FF6B6B")
        
        # 6. 稳态误差 (Ess)
        steady_errors = errors[-min(50, len(errors)):]
        steady_error = np.mean(np.abs(steady_errors))
        self._steady_error_card.set_value(steady_error)
    
    def _calculate_dynamic_metrics(self, timestamps, setpoints, process_values, errors):
        """计算动态特性指标"""
        if len(timestamps) < 20:
            return
        
        # 振荡次数
        zero_crossings = np.where(np.diff(np.signbit(errors)))[0]
        oscillations = len(zero_crossings) // 2
        status = "振荡" if oscillations > 5 else ("适中" if oscillations > 2 else "稳定")
        color = "#FF6B6B" if oscillations > 5 else ("#FFE66D" if oscillations > 2 else "#4ECDC4")
        self._oscillation_card.set_value(oscillations, status_color=color, status_text=status)
        
        # 找到峰值用于计算阻尼比和自然频率
        sp_mean = np.mean(setpoints)
        pv_centered = process_values - sp_mean
        
        # 找局部极值
        peaks = []
        for i in range(1, len(pv_centered) - 1):
            if pv_centered[i] > pv_centered[i-1] and pv_centered[i] > pv_centered[i+1]:
                peaks.append((timestamps[i], pv_centered[i]))
            elif pv_centered[i] < pv_centered[i-1] and pv_centered[i] < pv_centered[i+1]:
                peaks.append((timestamps[i], pv_centered[i]))
        
        if len(peaks) >= 2:
            # 阻尼比 (ζ) - 从对数衰减率估算
            peak_values = [abs(p[1]) for p in peaks]
            if len(peak_values) >= 2 and peak_values[0] > 0 and peak_values[1] > 0:
                log_decrement = np.log(peak_values[0] / peak_values[1])
                if log_decrement > 0:
                    damping_ratio = log_decrement / np.sqrt(4 * np.pi**2 + log_decrement**2)
                    damping_ratio = min(1.0, max(0, damping_ratio))
                    status = "过阻尼" if damping_ratio > 0.8 else ("临界" if damping_ratio > 0.6 else ("欠阻尼" if damping_ratio < 0.4 else "良好"))
                    color = "#FFE66D" if damping_ratio > 0.8 or damping_ratio < 0.3 else "#4ECDC4"
                    self._damping_ratio_card.set_value(damping_ratio, status_color=color, status_text=status)
                    
                    # 衰减比
                    decay_ratio = peak_values[1] / peak_values[0] if peak_values[0] > 0 else 0
                    self._decay_ratio_card.set_value(decay_ratio)
                else:
                    self._damping_ratio_card.set_value("N/A")
                    self._decay_ratio_card.set_value("N/A")
            
            # 自然频率 (ωn) - 从振荡周期估算
            if len(peaks) >= 2:
                period = abs(peaks[1][0] - peaks[0][0]) * 2  # 两个连续峰值之间是半个周期
                if period > 0:
                    omega_d = 2 * np.pi / period  # 阻尼振荡频率
                    self._natural_freq_card.set_value(omega_d)
                else:
                    self._natural_freq_card.set_value("N/A")
        else:
            self._damping_ratio_card.set_value("N/A")
            self._natural_freq_card.set_value("N/A")
            self._decay_ratio_card.set_value("N/A")
    
    def _calculate_frequency_domain_metrics(self, timestamps, errors):
        """计算频域性能指标"""
        if len(timestamps) < 64:
            return
        
        dt = np.mean(np.diff(timestamps))
        if dt <= 0:
            return
        fs = 1.0 / dt
        
        # FFT
        n = len(errors)
        fft_result = np.fft.rfft(errors)
        freqs = np.fft.rfftfreq(n, dt)
        magnitude = np.abs(fft_result)
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # 归一化
        max_mag = np.max(magnitude_db)
        magnitude_db_norm = magnitude_db - max_mag
        
        # 更新波特图
        valid_idx = freqs > 0
        if np.any(valid_idx):
            self._bode_mag_curve.setData(freqs[valid_idx], magnitude_db_norm[valid_idx])
        
        # 1. 带宽 (BW) - -3dB点
        above_3db = np.where(magnitude_db_norm > -3)[0]
        if len(above_3db) > 0:
            bandwidth_idx = above_3db[-1]
            bandwidth = freqs[bandwidth_idx] if bandwidth_idx < len(freqs) else 0
            self._bandwidth_card.set_value(bandwidth)
        else:
            self._bandwidth_card.set_value("N/A")
        
        # 2. 谐振峰值 (Mr) 和 3. 谐振频率 (ωr)
        if len(magnitude_db) > 1:
            peak_idx = np.argmax(magnitude_db[1:]) + 1
            resonance_peak = magnitude_db_norm[peak_idx]
            resonance_freq = freqs[peak_idx]
            self._resonance_card.set_value(resonance_peak)
            self._resonance_freq_card.set_value(resonance_freq)
        
        # 4. 截止频率 (ωc) - 幅值下降到0dB
        zero_crossings = np.where(np.diff(np.signbit(magnitude_db_norm)))[0]
        if len(zero_crossings) > 0:
            cutoff_idx = zero_crossings[0]
            cutoff_freq = freqs[cutoff_idx] if cutoff_idx < len(freqs) else 0
            self._cutoff_freq_card.set_value(cutoff_freq)
        else:
            self._cutoff_freq_card.set_value("N/A")
        
        # 5. 相位裕度估算 (PM) - 简化估算
        # 从阻尼比估算: PM ≈ 100 * ζ (对于ζ < 0.7)
        # 这里使用带宽和谐振峰值来估算
        if len(above_3db) > 0 and resonance_peak > -3:
            # 简化估算: PM ≈ 60° - 10*Mr(dB) 对于典型系统
            pm_estimate = max(0, min(90, 60 - 10 * resonance_peak))
            status = "良好" if pm_estimate > 45 else ("一般" if pm_estimate > 30 else "差")
            color = "#4ECDC4" if pm_estimate > 45 else ("#FFE66D" if pm_estimate > 30 else "#FF6B6B")
            self._phase_margin_card.set_value(pm_estimate, status_color=color, status_text=status)
        else:
            self._phase_margin_card.set_value("N/A")
        
        # 6. 增益裕度估算 (GM)
        # 简化估算基于高频衰减
        high_freq_idx = int(len(freqs) * 0.8)
        if high_freq_idx < len(magnitude_db_norm):
            high_freq_mag = np.mean(magnitude_db_norm[high_freq_idx:])
            gain_margin = abs(high_freq_mag)
            status = "良好" if gain_margin > 10 else ("一般" if gain_margin > 6 else "差")
            color = "#4ECDC4" if gain_margin > 10 else ("#FFE66D" if gain_margin > 6 else "#FF6B6B")
            self._gain_margin_card.set_value(gain_margin, status_color=color, status_text=status)
        else:
            self._gain_margin_card.set_value("N/A")
    
    def _calculate_statistical_metrics(self, timestamps, errors):
        """计算统计与质量指标（现代控制）"""
        if len(timestamps) < 10:
            return
        
        dt = np.mean(np.diff(timestamps))
        t = timestamps - timestamps[0]
        
        # 1. IAE - 积分绝对误差
        iae = np.trapezoid(np.abs(errors), timestamps)
        self._iae_card.set_value(iae)
        
        # 2. ISE - 积分平方误差
        ise = np.trapezoid(errors**2, timestamps)
        self._ise_card.set_value(ise)
        
        # 3. ITAE - 时间加权积分绝对误差
        itae = np.trapezoid(t * np.abs(errors), timestamps)
        self._itae_card.set_value(itae)
        
        # 4. RMSE - 均方根误差
        rmse = np.sqrt(np.mean(errors**2))
        self._rmse_card.set_value(rmse)
        
        # 5. MAE - 平均绝对误差
        mae = np.mean(np.abs(errors))
        self._mae_card.set_value(mae)
        
        # 6. 误差标准差
        std_error = np.std(errors)
        self._std_error_card.set_value(std_error)
    
    def _calculate_control_energy_metrics(self, timestamps, outputs):
        """计算控制能量指标"""
        if len(timestamps) < 10 or len(outputs) < 10:
            return
        
        dt = np.mean(np.diff(timestamps))
        
        # 1. 控制能量 - ∫u²dt
        control_effort = np.trapezoid(outputs**2, timestamps)
        self._control_effort_card.set_value(control_effort)
        
        # 2. 最大控制量
        max_control = np.max(np.abs(outputs))
        self._max_control_card.set_value(max_control)
        
        # 3. 控制量方差
        control_variance = np.var(outputs)
        self._control_variance_card.set_value(control_variance)
        
        # 4. 平滑度 - ∫(du/dt)²dt
        if len(outputs) > 1:
            du_dt = np.diff(outputs) / dt
            smoothness = np.trapezoid(du_dt**2, timestamps[:-1])
            self._smoothness_card.set_value(smoothness)
        else:
            self._smoothness_card.set_value("N/A")
    
    def _update_error_histogram(self, errors):
        """更新误差直方图"""
        self._error_hist_plot.clear()
        
        if len(errors) < 10:
            return
        
        # 计算直方图
        hist, bins = np.histogram(errors, bins=50)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # 绘制柱状图
        bargraph = pg.BarGraphItem(x=bin_centers, height=hist, width=(bins[1]-bins[0])*0.8, 
                                   brush='#4ECDC4', pen=pg.mkPen('#2D9C8C'))
        self._error_hist_plot.addItem(bargraph)
        
        # 添加正态分布拟合曲线
        mean = np.mean(errors)
        std = np.std(errors)
        if std > 0:
            x_fit = np.linspace(bins[0], bins[-1], 100)
            y_fit = len(errors) * (bins[1] - bins[0]) * (1/(std * np.sqrt(2*np.pi))) * np.exp(-0.5*((x_fit-mean)/std)**2)
            self._error_hist_plot.plot(x_fit, y_fit, pen=pg.mkPen('#FF6B6B', width=2))
    
    def _calculate_stability_score(self, timestamps, setpoints, process_values, errors):
        """计算综合稳定性评分"""
        score = 100
        status_parts = []
        
        if len(errors) < 10:
            self._stability_gauge.set_score(0, "数据不足")
            return
        
        # 1. 稳态误差评分 (30分)
        steady_errors = errors[-min(50, len(errors)):]
        steady_error = np.mean(np.abs(steady_errors))
        sp_range = np.max(setpoints) - np.min(setpoints)
        if sp_range > 0:
            error_ratio = steady_error / sp_range
        else:
            error_ratio = steady_error
        
        if error_ratio < 0.01:
            score -= 0
        elif error_ratio < 0.05:
            score -= 10
        elif error_ratio < 0.1:
            score -= 20
        else:
            score -= 30
            status_parts.append("稳态误差大")
        
        # 2. 振荡评分 (25分)
        zero_crossings = np.where(np.diff(np.signbit(errors)))[0]
        oscillations = len(zero_crossings) // 2
        if oscillations <= 2:
            score -= 0
        elif oscillations <= 5:
            score -= 10
        elif oscillations <= 10:
            score -= 20
        else:
            score -= 25
            status_parts.append("振荡过多")
        
        # 3. 超调评分 (25分)
        if len(setpoints) > 0:
            final_sp = setpoints[-1]
            delta = final_sp - process_values[0]
            if abs(delta) > 1e-6:
                if delta > 0:
                    overshoot = max(0, (np.max(process_values) - final_sp) / abs(delta) * 100)
                else:
                    overshoot = max(0, (final_sp - np.min(process_values)) / abs(delta) * 100)
            else:
                overshoot = 0
            
            if overshoot < 5:
                score -= 0
            elif overshoot < 15:
                score -= 10
            elif overshoot < 30:
                score -= 20
            else:
                score -= 25
                status_parts.append("超调过大")
        
        # 4. 噪声/抖动评分 (20分)
        noise_std = np.std(np.diff(errors))
        signal_range = np.max(errors) - np.min(errors)
        if signal_range > 0:
            snr = signal_range / (noise_std + 1e-10)
            if snr > 10:
                score -= 0
            elif snr > 5:
                score -= 5
            elif snr > 2:
                score -= 10
            else:
                score -= 20
                status_parts.append("噪声大")
        
        # 生成状态文字
        if score >= 80:
            status = "优秀 - 系统响应良好"
        elif score >= 60:
            status = "良好 - " + ", ".join(status_parts) if status_parts else "良好"
        elif score >= 40:
            status = "一般 - " + ", ".join(status_parts) if status_parts else "一般"
        else:
            status = "差 - " + ", ".join(status_parts) if status_parts else "需要调整"
        
        self._stability_gauge.set_score(score, status)
    
    def clear_all(self):
        """清空所有数据"""
        self._cached_data = {}
        self._response_curve.setData([], [])
        self._setpoint_curve.setData([], [])
        self._bode_mag_curve.setData([], [])
        self._error_hist_plot.clear()
        
        # 时域性能指标
        self._rise_time_card.clear()
        self._settling_time_card.clear()
        self._overshoot_card.clear()
        self._peak_time_card.clear()
        self._delay_time_card.clear()
        self._steady_error_card.clear()
        
        # 动态特性指标
        self._oscillation_card.clear()
        self._damping_ratio_card.clear()
        self._natural_freq_card.clear()
        self._decay_ratio_card.clear()
        
        # 频域性能指标
        self._bandwidth_card.clear()
        self._resonance_card.clear()
        self._resonance_freq_card.clear()
        self._cutoff_freq_card.clear()
        self._phase_margin_card.clear()
        self._gain_margin_card.clear()
        
        # 统计与质量指标
        self._iae_card.clear()
        self._ise_card.clear()
        self._itae_card.clear()
        self._rmse_card.clear()
        self._mae_card.clear()
        self._std_error_card.clear()
        
        # 控制能量指标
        self._control_effort_card.clear()
        self._max_control_card.clear()
        self._control_variance_card.clear()
        self._smoothness_card.clear()
        
        # 稳定性
        self._stability_gauge.clear()


class AnalysisWindow(QMainWindow):
    """独立的详细分析窗口 - 误差/控制输出/FFT"""
    
    COLORS = {
        'error': '#FFE66D',         # 黄色 - 误差
        'output': '#95E1D3',        # 绿色 - 控制输出
        'fft': '#DDA0DD',           # 紫色 - FFT
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 详细分析窗口 - 误差/输出/频谱")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel("📈 误差分析 / 控制输出 / 频域分析")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; padding: 5px;")
        layout.addWidget(title)
        
        self.error_plot = RealtimePlotWidget("误差曲线")
        self.error_plot.set_y_label("误差")
        self.error_plot.add_curve('误差', self.COLORS['error'], width=2)
        layout.addWidget(self.error_plot, stretch=1)
        
        self.output_plot = RealtimePlotWidget("控制输出")
        self.output_plot.set_y_label("输出")
        self.output_plot.add_curve('控制输出', self.COLORS['output'], width=2)
        layout.addWidget(self.output_plot, stretch=1)
        
        self.fft_plot = FFTPlotWidget()
        layout.addWidget(self.fft_plot, stretch=1)
    
    def update_data(self, timestamps: np.ndarray, setpoints: np.ndarray,
                    process_values: np.ndarray, errors: np.ndarray,
                    outputs: np.ndarray):
        if len(timestamps) == 0:
            return
        self.error_plot.update_curve('误差', timestamps, errors)
        self.output_plot.update_curve('控制输出', timestamps, outputs)

    def update_fft(self, frequencies: np.ndarray, magnitudes: np.ndarray):
        if len(frequencies) > 0:
            self.fft_plot.update_data(frequencies, magnitudes)
    
    def clear_all(self):
        self.error_plot.clear_curves()
        self.output_plot.clear_curves()
        self.fft_plot.clear_curves()


class StandardResponseWidget(QWidget):
    """标准响应控制曲线组件（通用）- 简化版，只显示主响应曲线"""
    
    COLORS = {
        'setpoint': '#FF6B6B',      # 红色 - 设定值
        'process_value': '#4ECDC4', # 青色 - 过程值
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._analysis_window = None
        self._extended_window = None
        self._cached_data = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 系统响应曲线（SP vs PV）- 主图
        self.response_plot = RealtimePlotWidget("系统响应曲线 (目标值 vs 当前值)")
        self.response_plot.set_y_label("数值")
        self.response_plot.add_curve('目标值', self.COLORS['setpoint'], width=2)
        self.response_plot.add_curve('当前值', self.COLORS['process_value'], width=2)
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
    
    def _open_analysis_window(self):
        """打开详细分析窗口"""
        if self._analysis_window is None or not self._analysis_window.isVisible():
            self._analysis_window = AnalysisWindow(self)
            if self._cached_data:
                self._analysis_window.update_data(**self._cached_data)
        self._analysis_window.show()
        self._analysis_window.raise_()
        self._analysis_window.activateWindow()
    
    def _open_extended_window(self):
        """打开扩展分析窗口"""
        if self._extended_window is None or not self._extended_window.isVisible():
            self._extended_window = ExtendedAnalysisWindow(self)
            if self._cached_data:
                self._extended_window.update_data(**self._cached_data)
        self._extended_window.show()
        self._extended_window.raise_()
        self._extended_window.activateWindow()
    
    def update_data(self, timestamps: np.ndarray, setpoints: np.ndarray,
                    process_values: np.ndarray, errors: np.ndarray, 
                    outputs: np.ndarray):
        """更新所有图表数据"""
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
        
        # 更新主界面图表（只有响应曲线）
        self.response_plot.update_curve('目标值', timestamps, setpoints)
        self.response_plot.update_curve('当前值', timestamps, process_values)

        # 更新详细分析窗口（如果打开）
        if self._analysis_window and self._analysis_window.isVisible():
            self._analysis_window.update_data(**self._cached_data)
        
        # 更新扩展分析窗口（如果打开）
        if self._extended_window and self._extended_window.isVisible():
            self._extended_window.update_data(**self._cached_data)
    
    def update_fft(self, frequencies: np.ndarray, magnitudes: np.ndarray):
        """更新FFT数据"""
        if self._analysis_window and self._analysis_window.isVisible():
            self._analysis_window.update_fft(frequencies, magnitudes)
    
    def close_analysis_window(self):
        """关闭所有分析窗口"""
        if self._analysis_window:
            self._analysis_window.close()
            self._analysis_window = None
        if self._extended_window:
            self._extended_window.close()
            self._extended_window = None
    
    def clear_all(self):
        """清空所有图表"""
        self.response_plot.clear_curves()
        # 清空分析窗口
        if self._analysis_window:
            self._analysis_window.clear_all()
        if self._extended_window:
            self._extended_window.clear_all()
        self._cached_data = None


class SimulatorPlotWidget(QWidget):
    """仿真数据绘图组件 - 支持状态选择"""

    # 信号：当选择的状态改变时发出
    state_selection_changed = pyqtSignal(int)  # 选中的状态索引

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_system = None
        self._state_defs = []  # 状态定义列表
        self._selected_state_index = 0  # 当前选中的状态索引
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 状态选择器区域
        selector_frame = QFrame()
        selector_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3C3C3C;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(10, 5, 10, 5)
        selector_layout.setSpacing(10)

        # 状态选择标签
        state_label = QLabel("📊 观察状态:")
        state_label.setStyleSheet("color: #FFFFFF; font-weight: bold; border: none;")
        selector_layout.addWidget(state_label)

        # 状态选择下拉框
        self._state_combo = QComboBox()
        self._state_combo.setMinimumWidth(200)
        self._state_combo.setStyleSheet("""
            QComboBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #0078D4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D30;
                color: #FFFFFF;
                selection-background-color: #0078D4;
            }
        """)
        self._state_combo.addItem("等待握手帧...")
        self._state_combo.setEnabled(False)
        self._state_combo.currentIndexChanged.connect(self._on_state_selected)
        selector_layout.addWidget(self._state_combo)

        # 当前状态信息显示
        self._state_info_label = QLabel("")
        self._state_info_label.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        selector_layout.addWidget(self._state_info_label)

        selector_layout.addStretch()

        # 系统类型显示
        self._system_label = QLabel("系统: --")
        self._system_label.setStyleSheet("color: #4FC3F7; font-size: 11px; border: none;")
        selector_layout.addWidget(self._system_label)

        layout.addWidget(selector_frame)

        # 标准响应控制曲线组件
        self.standard_plot = StandardResponseWidget()
        layout.addWidget(self.standard_plot, stretch=1)

    def _on_state_selected(self, index: int):
        """状态选择改变"""
        if index >= 0 and index < len(self._state_defs):
            self._selected_state_index = index
            state_def = self._state_defs[index]
            self._state_info_label.setText(f"单位: {state_def.get('unit', '--')} | {state_def.get('description', '')}")
            self.state_selection_changed.emit(index)

    def set_state_definitions(self, state_defs: list):
        """设置状态定义列表（从握手帧获取）"""
        self._state_defs = state_defs

        # 更新下拉框
        self._state_combo.blockSignals(True)
        self._state_combo.clear()

        if state_defs:
            for i, state in enumerate(state_defs):
                name = state.get('name', f'state_{i}')
                unit = state.get('unit', '')
                desc = state.get('description', '')
                display_text = f"{i}: {name}"
                if unit:
                    display_text += f" ({unit})"
                self._state_combo.addItem(display_text)

            self._state_combo.setEnabled(True)
            self._state_combo.setCurrentIndex(0)
            self._on_state_selected(0)
        else:
            self._state_combo.addItem("等待握手帧...")
            self._state_combo.setEnabled(False)
            self._state_info_label.setText("")

        self._state_combo.blockSignals(False)

    def get_selected_state_index(self) -> int:
        """获取当前选中的状态索引"""
        return self._selected_state_index

    def set_system_type(self, system_type):
        """设置系统类型"""
        self._current_system = system_type
        type_names = {
            'inverted_pendulum': '倒立摆系统',
            'ball_on_plate': '滚球控制系统',
            'unknown': '未知系统'
        }
        name = type_names.get(system_type, system_type)
        self._system_label.setText(f"系统: {name}")

    def clear_all(self):
        """清空所有图表"""
        self.standard_plot.clear_all()

    def clear_state_definitions(self):
        """清空状态定义（断开连接时调用）"""
        self._state_defs = []
        self._state_combo.blockSignals(True)
        self._state_combo.clear()
        self._state_combo.addItem("等待握手帧...")
        self._state_combo.setEnabled(False)
        self._state_combo.blockSignals(False)
        self._state_info_label.setText("")
        self._system_label.setText("系统: --")

