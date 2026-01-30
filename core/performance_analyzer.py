"""
性能分析模块
计算控制系统的各项性能指标
"""
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class PerformanceMetrics:
    """控制系统性能指标"""
    # 时域指标
    rise_time: Optional[float] = None          # 上升时间 (秒)
    settling_time: Optional[float] = None      # 调节时间 (秒)
    overshoot: Optional[float] = None          # 超调量 (%)
    peak_time: Optional[float] = None          # 峰值时间 (秒)
    peak_value: Optional[float] = None         # 峰值
    steady_state_error: Optional[float] = None # 稳态误差
    oscillation_count: int = 0                 # 振荡次数
    
    # 统计指标
    mean_error: Optional[float] = None         # 平均误差
    rms_error: Optional[float] = None          # 均方根误差
    max_error: Optional[float] = None          # 最大误差
    iae: Optional[float] = None                # 积分绝对误差
    ise: Optional[float] = None                # 积分平方误差
    itae: Optional[float] = None               # 时间加权积分绝对误差


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self._settling_threshold = 0.02  # 2% 稳态误差阈值
        self._rise_threshold = (0.1, 0.9)  # 上升时间定义: 10% ~ 90%
    
    def analyze(self, timestamps: np.ndarray, setpoints: np.ndarray, 
                process_values: np.ndarray, errors: np.ndarray) -> PerformanceMetrics:
        """
        分析系统性能
        
        Args:
            timestamps: 时间戳数组
            setpoints: 设定值数组
            process_values: 过程值数组
            errors: 误差数组
            
        Returns:
            PerformanceMetrics: 性能指标
        """
        metrics = PerformanceMetrics()
        
        if len(timestamps) < 10:
            return metrics
        
        # 计算基本统计指标
        metrics.mean_error = float(np.mean(np.abs(errors)))
        metrics.rms_error = float(np.sqrt(np.mean(errors ** 2)))
        metrics.max_error = float(np.max(np.abs(errors)))
        
        # 计算积分指标
        dt = np.diff(timestamps)
        if len(dt) > 0:
            avg_dt = np.mean(dt)
            metrics.iae = float(np.sum(np.abs(errors[:-1]) * dt))
            metrics.ise = float(np.sum(errors[:-1] ** 2 * dt))
            metrics.itae = float(np.sum(timestamps[:-1] * np.abs(errors[:-1]) * dt))
        
        # 检测阶跃响应（需要设定值有明显变化）
        sp_diff = np.diff(setpoints)
        step_indices = np.where(np.abs(sp_diff) > 0.1 * np.max(np.abs(setpoints) + 1e-6))[0]
        
        if len(step_indices) > 0:
            # 使用最后一个阶跃
            step_idx = step_indices[-1]
            self._analyze_step_response(
                timestamps[step_idx:], 
                setpoints[step_idx:], 
                process_values[step_idx:],
                metrics
            )
        
        # 计算稳态误差（使用最后10%的数据）
        n_steady = max(10, len(errors) // 10)
        metrics.steady_state_error = float(np.mean(errors[-n_steady:]))
        
        # 计算振荡次数
        metrics.oscillation_count = self._count_oscillations(errors)
        
        return metrics
    
    def _analyze_step_response(self, timestamps: np.ndarray, setpoints: np.ndarray,
                               process_values: np.ndarray, metrics: PerformanceMetrics):
        """分析阶跃响应特性"""
        if len(timestamps) < 5:
            return
        
        # 起始和目标值
        initial_value = process_values[0]
        final_sp = setpoints[-1]
        step_size = final_sp - initial_value
        
        if abs(step_size) < 1e-6:
            return
        
        # 归一化响应
        normalized = (process_values - initial_value) / step_size
        t = timestamps - timestamps[0]
        
        # 上升时间 (10% ~ 90%)
        try:
            idx_10 = np.where(normalized >= self._rise_threshold[0])[0]
            idx_90 = np.where(normalized >= self._rise_threshold[1])[0]
            if len(idx_10) > 0 and len(idx_90) > 0:
                metrics.rise_time = float(t[idx_90[0]] - t[idx_10[0]])
        except:
            pass
        
        # 峰值和峰值时间
        if step_size > 0:
            peak_idx = np.argmax(process_values)
        else:
            peak_idx = np.argmin(process_values)
        
        metrics.peak_value = float(process_values[peak_idx])
        metrics.peak_time = float(t[peak_idx])
        
        # 超调量
        if step_size > 0:
            overshoot = (process_values[peak_idx] - final_sp) / abs(step_size) * 100
        else:
            overshoot = (final_sp - process_values[peak_idx]) / abs(step_size) * 100
        metrics.overshoot = max(0, float(overshoot))
        
        # 调节时间（进入±2%稳态范围的时间）
        settling_band = abs(step_size) * self._settling_threshold
        in_band = np.abs(process_values - final_sp) <= settling_band
        
        # 从后往前找第一个出界的点
        for i in range(len(in_band) - 1, -1, -1):
            if not in_band[i]:
                if i < len(t) - 1:
                    metrics.settling_time = float(t[i + 1])
                break
    
    def _count_oscillations(self, errors: np.ndarray) -> int:
        """计算误差的振荡次数（过零次数）"""
        if len(errors) < 3:
            return 0
        
        # 计算符号变化次数
        signs = np.sign(errors)
        sign_changes = np.diff(signs)
        zero_crossings = np.sum(sign_changes != 0)
        
        # 振荡次数约为过零次数的一半
        return int(zero_crossings // 2)
    
    def compute_fft(self, timestamps: np.ndarray, signal_data: np.ndarray
                    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算信号的FFT
        
        Returns:
            (frequencies, magnitudes): 频率和幅值数组
        """
        if len(timestamps) < 10:
            return np.array([]), np.array([])
        
        # 计算采样频率
        dt = np.mean(np.diff(timestamps))
        if dt <= 0:
            return np.array([]), np.array([])
        
        fs = 1.0 / dt
        n = len(signal_data)
        
        # 去除直流分量
        signal_centered = signal_data - np.mean(signal_data)
        
        # 应用汉宁窗减少频谱泄漏
        window = np.hanning(n)
        signal_windowed = signal_centered * window
        
        # 计算FFT
        fft_result = fft(signal_windowed)
        frequencies = fftfreq(n, dt)
        
        # 只取正频率部分
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitudes = 2.0 / n * np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitudes
    
    def compute_psd(self, timestamps: np.ndarray, signal_data: np.ndarray
                    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算功率谱密度
        
        Returns:
            (frequencies, psd): 频率和功率谱密度数组
        """
        if len(timestamps) < 64:
            return np.array([]), np.array([])
        
        dt = np.mean(np.diff(timestamps))
        if dt <= 0:
            return np.array([]), np.array([])
        
        fs = 1.0 / dt
        
        # 使用 Welch 方法计算 PSD
        nperseg = min(256, len(signal_data) // 4)
        if nperseg < 16:
            return np.array([]), np.array([])
        
        frequencies, psd = signal.welch(signal_data, fs=fs, nperseg=nperseg)
        
        return frequencies, psd
