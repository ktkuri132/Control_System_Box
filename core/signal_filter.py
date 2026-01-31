"""
信号滤波模块
支持多种滤波算法、强度调节、算法融合
"""
import numpy as np
from scipy import signal
from scipy.ndimage import uniform_filter1d
from typing import List, Tuple, Optional
from collections import deque


class FilterType:
    """滤波器类型"""
    NONE = "无滤波"
    MOVING_AVERAGE = "移动平均"
    EXPONENTIAL = "指数平滑"
    LOWPASS = "低通滤波"
    MEDIAN = "中值滤波"
    KALMAN = "卡尔曼滤波"
    FUSION = "融合滤波"


class KalmanFilter1D:
    """一维卡尔曼滤波器"""

    def __init__(self, process_variance=1e-5, measurement_variance=1e-2):
        self.process_variance = process_variance  # 过程噪声
        self.measurement_variance = measurement_variance  # 测量噪声
        self.estimate = 0.0
        self.estimate_error = 1.0
        self.initialized = False

    def update(self, measurement: float) -> float:
        if not self.initialized:
            self.estimate = measurement
            self.initialized = True
            return measurement

        # 预测
        prediction = self.estimate
        prediction_error = self.estimate_error + self.process_variance

        # 更新
        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimate

    def reset(self):
        self.estimate = 0.0
        self.estimate_error = 1.0
        self.initialized = False


class SignalFilter:
    """信号滤波器"""

    def __init__(self):
        self._filter_type = FilterType.NONE
        self._strength = 5  # 滤波强度 1-10
        self._enabled = False

        # 各类滤波器的缓冲区
        self._buffer = deque(maxlen=100)
        self._kalman = KalmanFilter1D()
        self._last_ema = None  # 指数平滑上一个值

        # 低通滤波器系数
        self._lowpass_b = None
        self._lowpass_a = None
        self._lowpass_zi = None
        self._update_lowpass_coeffs()

        # 融合权重
        self._fusion_weights = {
            FilterType.MOVING_AVERAGE: 0.3,
            FilterType.EXPONENTIAL: 0.3,
            FilterType.KALMAN: 0.4
        }

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        if value:
            self.reset()

    @property
    def filter_type(self) -> str:
        return self._filter_type

    @filter_type.setter
    def filter_type(self, value: str):
        self._filter_type = value
        self.reset()

    def get_filter_type_key(self) -> str:
        """获取滤波器类型的英文键名（用于多进程处理）"""
        type_map = {
            FilterType.NONE: 'none',
            FilterType.MOVING_AVERAGE: 'moving_average',
            FilterType.EXPONENTIAL: 'exponential',
            FilterType.LOWPASS: 'butterworth',
            FilterType.MEDIAN: 'median',
            FilterType.KALMAN: 'kalman',
            FilterType.FUSION: 'moving_average',  # 融合默认用移动平均
        }
        return type_map.get(self._filter_type, 'none')

    @property
    def strength(self) -> int:
        return self._strength

    @strength.setter
    def strength(self, value: int):
        self._strength = max(1, min(10, value))
        self._update_lowpass_coeffs()

    @property
    def window_size(self) -> int:
        """滤波窗口大小（根据强度计算）"""
        return self._strength * 2 + 1

    def _update_lowpass_coeffs(self):
        """更新低通滤波器系数"""
        # 截止频率根据强度调整 (强度越大，截止频率越低)
        cutoff = 0.5 - (self._strength - 1) * 0.045  # 0.5 -> 0.095
        cutoff = max(0.05, min(0.5, cutoff))
        try:
            self._lowpass_b, self._lowpass_a = signal.butter(2, cutoff, btype='low')
            self._lowpass_zi = signal.lfilter_zi(self._lowpass_b, self._lowpass_a)
        except:
            self._lowpass_b = [1.0]
            self._lowpass_a = [1.0]
            self._lowpass_zi = np.array([0.0])

    def reset(self):
        """重置滤波器状态"""
        self._buffer.clear()
        self._kalman.reset()
        self._last_ema = None
        self._update_lowpass_coeffs()

    def filter(self, value: float) -> float:
        """
        对单个值进行滤波
        """
        if not self._enabled or self._filter_type == FilterType.NONE:
            return value

        self._buffer.append(value)

        if self._filter_type == FilterType.MOVING_AVERAGE:
            return self._moving_average(value)
        elif self._filter_type == FilterType.EXPONENTIAL:
            return self._exponential_smoothing(value)
        elif self._filter_type == FilterType.LOWPASS:
            return self._lowpass_filter(value)
        elif self._filter_type == FilterType.MEDIAN:
            return self._median_filter(value)
        elif self._filter_type == FilterType.KALMAN:
            return self._kalman_filter(value)
        elif self._filter_type == FilterType.FUSION:
            return self._fusion_filter(value)

        return value

    def _moving_average(self, value: float) -> float:
        """移动平均滤波"""
        window = self._strength * 2 + 1  # 3-21
        if len(self._buffer) < window:
            return np.mean(list(self._buffer))
        return np.mean(list(self._buffer)[-window:])

    def _exponential_smoothing(self, value: float) -> float:
        """指数平滑滤波"""
        alpha = 1.0 / (self._strength + 1)  # 0.5 -> 0.09
        if self._last_ema is None:
            self._last_ema = value
        else:
            self._last_ema = alpha * value + (1 - alpha) * self._last_ema
        return self._last_ema

    def _lowpass_filter(self, value: float) -> float:
        """低通滤波"""
        try:
            filtered, self._lowpass_zi = signal.lfilter(
                self._lowpass_b, self._lowpass_a, [value], zi=self._lowpass_zi * value
            )
            return filtered[0]
        except:
            return value

    def _median_filter(self, value: float) -> float:
        """中值滤波"""
        window = self._strength * 2 + 1
        if len(self._buffer) < window:
            return np.median(list(self._buffer))
        return np.median(list(self._buffer)[-window:])

    def _kalman_filter(self, value: float) -> float:
        """卡尔曼滤波"""
        # 根据强度调整测量噪声
        self._kalman.measurement_variance = 10 ** (-(self._strength - 5) / 2)
        return self._kalman.update(value)

    def _fusion_filter(self, value: float) -> float:
        """融合滤波 - 结合多种滤波器"""
        ma = self._moving_average(value)
        ema = self._exponential_smoothing(value)
        kalman = self._kalman.update(value)

        # 加权融合
        result = (
            self._fusion_weights[FilterType.MOVING_AVERAGE] * ma +
            self._fusion_weights[FilterType.EXPONENTIAL] * ema +
            self._fusion_weights[FilterType.KALMAN] * kalman
        )
        return result

    def filter_array(self, data: np.ndarray) -> np.ndarray:
        """
        对数组进行批量滤波
        """
        if not self._enabled or self._filter_type == FilterType.NONE:
            return data

        if len(data) == 0:
            return data

        if self._filter_type == FilterType.MOVING_AVERAGE:
            window = self._strength * 2 + 1
            return uniform_filter1d(data, size=window, mode='nearest')

        elif self._filter_type == FilterType.EXPONENTIAL:
            alpha = 1.0 / (self._strength + 1)
            result = np.zeros_like(data)
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
            return result

        elif self._filter_type == FilterType.LOWPASS:
            try:
                return signal.filtfilt(self._lowpass_b, self._lowpass_a, data)
            except:
                return data

        elif self._filter_type == FilterType.MEDIAN:
            window = self._strength * 2 + 1
            return signal.medfilt(data, kernel_size=window)

        elif self._filter_type == FilterType.KALMAN:
            result = np.zeros_like(data)
            kalman = KalmanFilter1D(
                measurement_variance=10 ** (-(self._strength - 5) / 2)
            )
            for i, v in enumerate(data):
                result[i] = kalman.update(v)
            return result

        elif self._filter_type == FilterType.FUSION:
            # 融合多种滤波结果
            window = self._strength * 2 + 1
            ma = uniform_filter1d(data, size=window, mode='nearest')

            alpha = 1.0 / (self._strength + 1)
            ema = np.zeros_like(data)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

            kalman_result = np.zeros_like(data)
            kalman = KalmanFilter1D(
                measurement_variance=10 ** (-(self._strength - 5) / 2)
            )
            for i, v in enumerate(data):
                kalman_result[i] = kalman.update(v)

            return (
                self._fusion_weights[FilterType.MOVING_AVERAGE] * ma +
                self._fusion_weights[FilterType.EXPONENTIAL] * ema +
                self._fusion_weights[FilterType.KALMAN] * kalman_result
            )

        return data


class HarmonicAnalyzer:
    """谐波分析器"""

    def __init__(self, sample_rate: float = 100.0):
        self.sample_rate = sample_rate

    def analyze(self, data: np.ndarray) -> dict:
        """
        对信号进行谐波分析
        返回: {
            'frequencies': 频率数组,
            'magnitudes': 幅值数组,
            'phases': 相位数组,
            'harmonics': [(频率, 幅值, 相位), ...] 主要谐波列表,
            'thd': 总谐波失真
        }
        """
        if len(data) < 10:
            return {
                'frequencies': np.array([]),
                'magnitudes': np.array([]),
                'phases': np.array([]),
                'harmonics': [],
                'thd': 0.0
            }

        # 去除直流分量
        data = data - np.mean(data)

        # FFT
        n = len(data)
        fft_result = np.fft.rfft(data)
        frequencies = np.fft.rfftfreq(n, 1.0 / self.sample_rate)
        magnitudes = np.abs(fft_result) * 2 / n
        phases = np.angle(fft_result)

        # 找基频 (最大幅值对应的频率，排除直流)
        if len(magnitudes) > 1:
            fundamental_idx = np.argmax(magnitudes[1:]) + 1
            fundamental_freq = frequencies[fundamental_idx]
            fundamental_mag = magnitudes[fundamental_idx]
        else:
            fundamental_freq = 0
            fundamental_mag = 0

        # 提取主要谐波 (幅值大于基频5%的)
        harmonics = []
        threshold = fundamental_mag * 0.05 if fundamental_mag > 0 else 0

        for i, (freq, mag, phase) in enumerate(zip(frequencies, magnitudes, phases)):
            if mag > threshold and freq > 0:
                harmonics.append({
                    'frequency': freq,
                    'magnitude': mag,
                    'phase': np.degrees(phase),
                    'order': round(freq / fundamental_freq) if fundamental_freq > 0 else 0
                })

        # 按幅值排序，取前10个
        harmonics.sort(key=lambda x: x['magnitude'], reverse=True)
        harmonics = harmonics[:10]

        # 计算总谐波失真 (THD)
        if fundamental_mag > 0 and len(magnitudes) > fundamental_idx:
            harmonic_power = np.sum(magnitudes[fundamental_idx+1:] ** 2)
            thd = np.sqrt(harmonic_power) / fundamental_mag * 100
        else:
            thd = 0.0

        return {
            'frequencies': frequencies,
            'magnitudes': magnitudes,
            'phases': phases,
            'harmonics': harmonics,
            'thd': thd,
            'fundamental_freq': fundamental_freq,
            'fundamental_mag': fundamental_mag
        }

    def decompose_harmonics(self, data: np.ndarray, num_harmonics: int = 5) -> List[np.ndarray]:
        """
        谐波分解 - 将信号分解为各次谐波分量
        返回: [基波, 2次谐波, 3次谐波, ...]
        """
        analysis = self.analyze(data)

        if len(analysis['harmonics']) == 0:
            return [data]

        n = len(data)
        t = np.arange(n) / self.sample_rate

        # 按谐波次数排序
        harmonics_by_order = {}
        for h in analysis['harmonics']:
            order = h['order']
            if order > 0 and order not in harmonics_by_order:
                harmonics_by_order[order] = h

        # 重建各次谐波
        result = []
        for order in range(1, num_harmonics + 1):
            if order in harmonics_by_order:
                h = harmonics_by_order[order]
                wave = h['magnitude'] * np.cos(
                    2 * np.pi * h['frequency'] * t + np.radians(h['phase'])
                )
                result.append(wave)
            else:
                result.append(np.zeros(n))

        return result


# 全局滤波器实例（每个状态通道一个）
_filters = {}

def get_filter(channel_id: int) -> SignalFilter:
    """获取指定通道的滤波器"""
    if channel_id not in _filters:
        _filters[channel_id] = SignalFilter()
    return _filters[channel_id]

def set_all_filters_enabled(enabled: bool):
    """设置所有滤波器启用状态"""
    for f in _filters.values():
        f.enabled = enabled

def set_all_filters_type(filter_type: str):
    """设置所有滤波器类型"""
    for f in _filters.values():
        f.filter_type = filter_type

def set_all_filters_strength(strength: int):
    """设置所有滤波器强度"""
    for f in _filters.values():
        f.strength = strength

def reset_all_filters():
    """重置所有滤波器"""
    for f in _filters.values():
        f.reset()
