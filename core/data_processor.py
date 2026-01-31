"""
高性能数据处理模块
使用多线程处理数据以提高性能
"""
import numpy as np
from typing import Dict, Callable, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QMutex, QMutexLocker
from collections import deque
import time


class DataProcessor(QThread):
    """后台数据处理线程"""

    # 信号：处理完成
    data_processed = pyqtSignal(dict)  # 处理后的数据字典

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._running = True
        self._has_new_data = False

        # 原始数据缓冲
        self._raw_timestamps = None
        self._raw_states = None
        self._selected_idx = 0

        # 滤波设置
        self._filter_enabled = False
        self._filter_func = None

    def set_data(self, timestamps: np.ndarray, states: list, selected_idx: int):
        """设置待处理的数据"""
        with QMutexLocker(self._mutex):
            self._raw_timestamps = timestamps.copy() if timestamps is not None else None
            self._raw_states = states.copy() if states else None
            self._selected_idx = selected_idx
            self._has_new_data = True

    def set_filter(self, enabled: bool, filter_func: Callable = None):
        """设置滤波器"""
        with QMutexLocker(self._mutex):
            self._filter_enabled = enabled
            self._filter_func = filter_func

    def stop(self):
        """停止线程"""
        self._running = False
        self.wait()

    def run(self):
        """线程主循环"""
        while self._running:
            if self._has_new_data:
                self._process_data()
            else:
                self.msleep(10)  # 没有数据时休眠

    def _process_data(self):
        """处理数据"""
        with QMutexLocker(self._mutex):
            if self._raw_timestamps is None or self._raw_states is None:
                self._has_new_data = False
                return

            timestamps = self._raw_timestamps
            states = self._raw_states
            selected_idx = self._selected_idx
            filter_enabled = self._filter_enabled
            filter_func = self._filter_func
            self._has_new_data = False

        try:
            n = len(timestamps)

            # 预分配数组
            setpoints = np.empty(n, dtype=np.float64)
            raw_values = np.empty(n, dtype=np.float64)

            # 快速提取数据
            for i, state_dict in enumerate(states):
                if selected_idx in state_dict:
                    setpoints[i] = state_dict[selected_idx]['target']
                    raw_values[i] = state_dict[selected_idx]['current']
                else:
                    setpoints[i] = 0.0
                    raw_values[i] = 0.0

            # 应用滤波
            if filter_enabled and filter_func is not None:
                process_values = filter_func(raw_values)
            else:
                process_values = raw_values

            errors = setpoints - process_values

            # 提取输出（最后一个状态）
            outputs = np.zeros(n, dtype=np.float64)
            if states and len(states[-1]) > 1:
                last_idx = max(states[-1].keys())
                for i, state_dict in enumerate(states):
                    if last_idx in state_dict:
                        outputs[i] = state_dict[last_idx]['current']

            # 发送处理结果
            result = {
                'timestamps': timestamps,
                'setpoints': setpoints,
                'process_values': process_values,
                'raw_values': raw_values if filter_enabled else None,
                'errors': errors,
                'outputs': outputs
            }
            self.data_processed.emit(result)

        except Exception as e:
            print(f"[DataProcessor] 处理错误: {e}")


class HighPerformanceBuffer:
    """高性能数据缓冲区 - 使用预分配的 numpy 数组"""

    def __init__(self, max_size: int = 50000):
        self.max_size = max_size
        self._size = 0

        # 预分配时间戳数组
        self._timestamps = np.zeros(max_size, dtype=np.float64)

        # 状态数据使用 deque（因为结构复杂）
        self._states = deque(maxlen=max_size)

        # 写入位置（环形缓冲）
        self._write_pos = 0
        self._is_full = False

    def append(self, timestamp: float, states: dict):
        """添加数据点"""
        self._timestamps[self._write_pos] = timestamp
        self._states.append(states)

        self._write_pos += 1
        if self._write_pos >= self.max_size:
            self._write_pos = 0
            self._is_full = True

        if not self._is_full:
            self._size = self._write_pos
        else:
            self._size = self.max_size

    def get_data(self, n: int = None) -> tuple:
        """获取最近 n 个数据点"""
        if self._size == 0:
            return np.array([]), []

        if n is None or n > self._size:
            n = self._size

        # 获取时间戳
        if self._is_full:
            # 环形缓冲区：需要处理回绕
            if self._write_pos >= n:
                timestamps = self._timestamps[self._write_pos - n:self._write_pos].copy()
            else:
                # 跨越边界
                part1 = self._timestamps[self.max_size - (n - self._write_pos):]
                part2 = self._timestamps[:self._write_pos]
                timestamps = np.concatenate([part1, part2])
        else:
            timestamps = self._timestamps[max(0, self._write_pos - n):self._write_pos].copy()

        # 获取状态（deque 已经自动处理了）
        states = list(self._states)[-n:]

        return timestamps, states

    def clear(self):
        """清空缓冲区"""
        self._size = 0
        self._write_pos = 0
        self._is_full = False
        self._timestamps.fill(0)
        self._states.clear()

    def __len__(self):
        return self._size


class PlotUpdateThrottler:
    """绑图更新节流器 - 限制更新频率"""

    def __init__(self, min_interval_ms: int = 33):  # 默认约 30 FPS
        self._min_interval = min_interval_ms / 1000.0
        self._last_update = 0

    def should_update(self) -> bool:
        """检查是否应该更新"""
        now = time.time()
        if now - self._last_update >= self._min_interval:
            self._last_update = now
            return True
        return False

    def set_fps(self, fps: int):
        """设置目标帧率"""
        self._min_interval = 1.0 / max(1, fps)


class DataDownsampler:
    """数据降采样器 - 用于高频数据的绑图"""

    @staticmethod
    def downsample_lttb(x: np.ndarray, y: np.ndarray, target_points: int) -> tuple:
        """
        使用 LTTB (Largest Triangle Three Buckets) 算法降采样
        保留数据的视觉特征
        """
        n = len(x)
        if n <= target_points:
            return x, y

        # 简化版 LTTB
        bucket_size = (n - 2) / (target_points - 2)

        result_x = np.zeros(target_points)
        result_y = np.zeros(target_points)

        # 第一个点
        result_x[0] = x[0]
        result_y[0] = y[0]

        for i in range(1, target_points - 1):
            # 当前桶的范围
            bucket_start = int((i - 1) * bucket_size) + 1
            bucket_end = int(i * bucket_size) + 1

            # 下一个桶的平均点
            next_bucket_start = int(i * bucket_size) + 1
            next_bucket_end = int((i + 1) * bucket_size) + 1
            next_bucket_end = min(next_bucket_end, n)

            avg_x = np.mean(x[next_bucket_start:next_bucket_end])
            avg_y = np.mean(y[next_bucket_start:next_bucket_end])

            # 在当前桶中找到与前一个点和下一个桶平均点形成最大三角形的点
            prev_x = result_x[i - 1]
            prev_y = result_y[i - 1]

            max_area = -1
            max_idx = bucket_start

            for j in range(bucket_start, min(bucket_end, n)):
                # 计算三角形面积
                area = abs((prev_x - avg_x) * (y[j] - prev_y) -
                          (prev_x - x[j]) * (avg_y - prev_y))
                if area > max_area:
                    max_area = area
                    max_idx = j

            result_x[i] = x[max_idx]
            result_y[i] = y[max_idx]

        # 最后一个点
        result_x[-1] = x[-1]
        result_y[-1] = y[-1]

        return result_x, result_y

    @staticmethod
    def downsample_minmax(x: np.ndarray, y: np.ndarray, target_points: int) -> tuple:
        """
        Min-Max 降采样 - 每个桶保留最小和最大值
        适合显示数据范围
        """
        n = len(x)
        if n <= target_points:
            return x, y

        # 每个桶的点数
        bucket_size = n // (target_points // 2)

        result_x = []
        result_y = []

        for i in range(0, n, bucket_size):
            bucket_end = min(i + bucket_size, n)
            bucket_y = y[i:bucket_end]
            bucket_x = x[i:bucket_end]

            if len(bucket_y) > 0:
                min_idx = np.argmin(bucket_y)
                max_idx = np.argmax(bucket_y)

                # 按时间顺序添加
                if min_idx <= max_idx:
                    result_x.extend([bucket_x[min_idx], bucket_x[max_idx]])
                    result_y.extend([bucket_y[min_idx], bucket_y[max_idx]])
                else:
                    result_x.extend([bucket_x[max_idx], bucket_x[min_idx]])
                    result_y.extend([bucket_y[max_idx], bucket_y[min_idx]])

        return np.array(result_x), np.array(result_y)
