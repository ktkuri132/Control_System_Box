"""
高性能多进程数据处理模块
使用 multiprocessing 绕开 GIL，充分利用多核 CPU
"""
import numpy as np
import multiprocessing as mp
from typing import Optional, Callable
import time
import queue
import threading
from concurrent.futures import ProcessPoolExecutor
import os

# 导入调试分析器
from core.debug_profiler import (
    DEBUG_MODE, profile_function, profile_method,
    ProfileBlock, debug_print, get_profiler
)

# 设置进程启动方式（Windows 必须使用 spawn）
# 注意：这个设置只能在主模块中调用一次
try:
    if os.name == 'nt':
        mp.set_start_method('spawn', force=True)
except RuntimeError:
    # 已经设置过了，忽略
    pass


# ============== 纯函数：在子进程中执行的计算任务 ==============

def _extract_data_task(states_data: list, selected_idx: int, n: int) -> tuple:
    """
    提取数据任务 - 在子进程中执行
    将字典列表转换为 numpy 数组
    """
    setpoints = np.empty(n, dtype=np.float64)
    raw_values = np.empty(n, dtype=np.float64)

    for i, state_dict in enumerate(states_data):
        if selected_idx in state_dict:
            setpoints[i] = state_dict[selected_idx]['target']
            raw_values[i] = state_dict[selected_idx]['current']
        else:
            setpoints[i] = 0.0
            raw_values[i] = 0.0

    return setpoints, raw_values


def _apply_filter_task(raw_values: np.ndarray, filter_type: str,
                       filter_strength: float, window_size: int) -> np.ndarray:
    """
    应用滤波任务 - 在子进程中执行
    """
    if filter_type == 'none' or len(raw_values) < 3:
        return raw_values.copy()

    n = len(raw_values)
    result = np.empty(n, dtype=np.float64)

    if filter_type == 'moving_average':
        # 移动平均滤波
        kernel = np.ones(window_size) / window_size
        # 使用 numpy 卷积，比循环快很多
        padded = np.pad(raw_values, (window_size//2, window_size//2), mode='edge')
        result = np.convolve(padded, kernel, mode='valid')[:n]

    elif filter_type == 'exponential':
        # 指数平滑滤波
        alpha = filter_strength
        result[0] = raw_values[0]
        for i in range(1, n):
            result[i] = alpha * raw_values[i] + (1 - alpha) * result[i-1]

    elif filter_type == 'median':
        # 中值滤波 - 使用滑动窗口
        half_win = window_size // 2
        for i in range(n):
            start = max(0, i - half_win)
            end = min(n, i + half_win + 1)
            result[i] = np.median(raw_values[start:end])

    elif filter_type == 'gaussian':
        # 高斯滤波
        sigma = window_size / 6.0
        x = np.arange(-window_size//2, window_size//2 + 1)
        kernel = np.exp(-x**2 / (2 * sigma**2))
        kernel = kernel / kernel.sum()
        padded = np.pad(raw_values, (window_size//2, window_size//2), mode='edge')
        result = np.convolve(padded, kernel, mode='valid')[:n]

    elif filter_type == 'butterworth':
        # 简化版低通滤波（避免 scipy 依赖问题）
        alpha = filter_strength
        result[0] = raw_values[0]
        if n > 1:
            result[1] = raw_values[1]
        for i in range(2, n):
            result[i] = (alpha * raw_values[i] +
                        alpha * raw_values[i-1] +
                        (1 - 2*alpha) * result[i-1])
    else:
        result = raw_values.copy()

    return result


def _compute_errors_task(setpoints: np.ndarray, process_values: np.ndarray) -> np.ndarray:
    """计算误差 - 在子进程中执行"""
    return setpoints - process_values


def _extract_outputs_task(states_data: list, n: int) -> np.ndarray:
    """提取输出 - 在子进程中执行"""
    outputs = np.zeros(n, dtype=np.float64)
    if states_data and len(states_data[-1]) > 1:
        last_idx = max(states_data[-1].keys())
        for i, state_dict in enumerate(states_data):
            if last_idx in state_dict:
                outputs[i] = state_dict[last_idx]['current']
    return outputs


def _downsample_lttb_task(x: np.ndarray, y: np.ndarray, target_points: int) -> tuple:
    """
    LTTB 降采样 - 在子进程中执行
    使用向量化操作优化
    """
    n = len(x)
    if n <= target_points:
        return x.copy(), y.copy()

    bucket_size = (n - 2) / (target_points - 2)

    result_x = np.zeros(target_points, dtype=np.float64)
    result_y = np.zeros(target_points, dtype=np.float64)

    result_x[0] = x[0]
    result_y[0] = y[0]
    result_x[-1] = x[-1]
    result_y[-1] = y[-1]

    for i in range(1, target_points - 1):
        bucket_start = int((i - 1) * bucket_size) + 1
        bucket_end = min(int(i * bucket_size) + 1, n)

        next_bucket_start = int(i * bucket_size) + 1
        next_bucket_end = min(int((i + 1) * bucket_size) + 1, n)

        if next_bucket_end > next_bucket_start:
            avg_x = np.mean(x[next_bucket_start:next_bucket_end])
            avg_y = np.mean(y[next_bucket_start:next_bucket_end])
        else:
            avg_x = x[-1]
            avg_y = y[-1]

        prev_x = result_x[i - 1]
        prev_y = result_y[i - 1]

        # 向量化计算三角形面积
        bucket_x = x[bucket_start:bucket_end]
        bucket_y = y[bucket_start:bucket_end]

        if len(bucket_x) > 0:
            areas = np.abs((prev_x - avg_x) * (bucket_y - prev_y) -
                          (prev_x - bucket_x) * (avg_y - prev_y))
            max_idx = np.argmax(areas)
            result_x[i] = bucket_x[max_idx]
            result_y[i] = bucket_y[max_idx]
        else:
            result_x[i] = x[bucket_start] if bucket_start < n else x[-1]
            result_y[i] = y[bucket_start] if bucket_start < n else y[-1]

    return result_x, result_y


def _full_process_task(timestamps: np.ndarray, states_data: list,
                       selected_idx: int, filter_type: str,
                       filter_strength: float, window_size: int,
                       downsample_target: int) -> dict:
    """
    完整的数据处理任务 - 在子进程中执行
    包含提取、滤波、降采样的完整流程
    """
    n = len(timestamps)

    # 1. 提取数据
    setpoints, raw_values = _extract_data_task(states_data, selected_idx, n)

    # 2. 应用滤波
    if filter_type and filter_type != 'none':
        process_values = _apply_filter_task(raw_values, filter_type,
                                           filter_strength, window_size)
    else:
        process_values = raw_values

    # 3. 计算误差
    errors = _compute_errors_task(setpoints, process_values)

    # 4. 提取输出
    outputs = _extract_outputs_task(states_data, n)

    # 5. 降采样（如果需要）
    if downsample_target > 0 and n > downsample_target:
        ts_down, setpoints_down = _downsample_lttb_task(timestamps, setpoints, downsample_target)
        _, pv_down = _downsample_lttb_task(timestamps, process_values, downsample_target)
        _, err_down = _downsample_lttb_task(timestamps, errors, downsample_target)
        _, out_down = _downsample_lttb_task(timestamps, outputs, downsample_target)

        # 原始值也要降采样
        if filter_type and filter_type != 'none':
            _, raw_down = _downsample_lttb_task(timestamps, raw_values, downsample_target)
        else:
            raw_down = None

        return {
            'timestamps': ts_down,
            'setpoints': setpoints_down,
            'process_values': pv_down,
            'raw_values': raw_down,
            'errors': err_down,
            'outputs': out_down
        }
    else:
        return {
            'timestamps': timestamps,
            'setpoints': setpoints,
            'process_values': process_values,
            'raw_values': raw_values if filter_type and filter_type != 'none' else None,
            'errors': errors,
            'outputs': outputs
        }


# ============== 多进程数据处理器 ==============

class MultiProcessDataProcessor:
    """
    多进程数据处理器
    使用进程池来处理 CPU 密集型计算，绕开 GIL
    """

    def __init__(self, num_workers: int = None, callback: Callable = None):
        """
        初始化处理器

        Args:
            num_workers: 工作进程数，默认为 CPU 核心数 - 1
            callback: 处理完成的回调函数
        """
        if num_workers is None:
            num_workers = max(1, mp.cpu_count() - 1)

        self._num_workers = num_workers
        self._callback = callback
        self._executor: Optional[ProcessPoolExecutor] = None
        self._running = False

        # 任务队列
        self._task_queue = queue.Queue(maxsize=2)  # 限制队列大小，避免积压
        self._result_thread: Optional[threading.Thread] = None

        # 滤波设置
        self._filter_type = 'none'
        self._filter_strength = 0.3
        self._window_size = 5

        # 降采样设置 - ★ 减少点数以提升渲染性能
        self._downsample_target = 500  # 进一步减少到 500 点

        # 性能统计
        self._process_times = []

    def start(self):
        """启动处理器"""
        if self._running:
            return

        self._running = True
        self._executor = ProcessPoolExecutor(max_workers=self._num_workers)

        # 启动结果处理线程
        self._result_thread = threading.Thread(target=self._result_worker, daemon=True)
        self._result_thread.start()

        print(f"[MultiProcessDataProcessor] 启动，使用 {self._num_workers} 个工作进程")

    def stop(self):
        """停止处理器"""
        self._running = False

        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

        # 清空队列
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break

    def set_filter(self, filter_type: str, strength: float = 0.3, window_size: int = 5):
        """设置滤波参数"""
        self._filter_type = filter_type
        self._filter_strength = strength
        self._window_size = window_size

    def set_downsample_target(self, target: int):
        """设置降采样目标点数"""
        self._downsample_target = target

    def set_callback(self, callback: Callable):
        """设置回调函数"""
        self._callback = callback

    def submit_task(self, timestamps: np.ndarray, states: list, selected_idx: int):
        """
        提交处理任务

        Args:
            timestamps: 时间戳数组
            states: 状态数据列表
            selected_idx: 选中的状态索引
        """
        if not self._running or self._executor is None:
            return False

        # 丢弃旧任务，只保留最新的
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break

        try:
            # 提交到进程池
            future = self._executor.submit(
                _full_process_task,
                timestamps.copy(),
                states.copy(),
                selected_idx,
                self._filter_type,
                self._filter_strength,
                self._window_size,
                self._downsample_target
            )

            self._task_queue.put((future, time.time()))
            return True

        except Exception as e:
            print(f"[MultiProcessDataProcessor] 提交任务失败: {e}")
            return False

    def _result_worker(self):
        """结果处理线程"""
        while self._running:
            try:
                item = self._task_queue.get(timeout=0.1)
                future, submit_time = item

                try:
                    result = future.result(timeout=2.0)  # 增加超时时间
                    process_time = time.time() - submit_time
                    self._process_times.append(process_time)

                    # 保留最近100次的处理时间
                    if len(self._process_times) > 100:
                        self._process_times = self._process_times[-100:]

                    if self._callback:
                        self._callback(result)
                    else:
                        print("[MultiProcessDataProcessor] 警告: 没有设置回调函数")

                except Exception as e:
                    print(f"[MultiProcessDataProcessor] 任务执行失败: {e}")
                    import traceback
                    traceback.print_exc()

            except queue.Empty:
                continue
            except Exception as e:
                if self._running:
                    print(f"[MultiProcessDataProcessor] 结果处理错误: {e}")

    def get_avg_process_time(self) -> float:
        """获取平均处理时间"""
        if not self._process_times:
            return 0.0
        return sum(self._process_times) / len(self._process_times)


# ============== 兼容旧接口的包装器 ==============

class DataProcessorWrapper:
    """
    数据处理器包装器
    提供与旧 DataProcessor 兼容的接口，内部使用多进程
    """

    def __init__(self):
        self._processor = MultiProcessDataProcessor()
        self._data_processed_callbacks = []

        # 滤波函数映射（用于兼容旧接口）
        self._filter_func = None
        self._filter_enabled = False

    def start(self):
        """启动处理器"""
        self._processor.set_callback(self._on_result)
        self._processor.start()

    def stop(self):
        """停止处理器"""
        self._processor.stop()

    def wait(self):
        """等待处理完成（兼容旧接口）"""
        pass

    def set_data(self, timestamps: np.ndarray, states: list, selected_idx: int):
        """设置待处理的数据"""
        self._processor.submit_task(timestamps, states, selected_idx)

    def set_filter(self, enabled: bool, filter_func: Callable = None):
        """设置滤波器（兼容旧接口）"""
        self._filter_enabled = enabled
        self._filter_func = filter_func

        # 从滤波函数推断类型（简化处理）
        if enabled and filter_func is not None:
            # 默认使用移动平均
            self._processor.set_filter('moving_average', 0.3, 5)
        else:
            self._processor.set_filter('none', 0.3, 5)

    def set_filter_params(self, filter_type: str, strength: float, window_size: int):
        """直接设置滤波参数"""
        if self._filter_enabled:
            self._processor.set_filter(filter_type, strength, window_size)
        else:
            self._processor.set_filter('none', strength, window_size)

    def connect_data_processed(self, callback: Callable):
        """连接数据处理完成信号"""
        self._data_processed_callbacks.append(callback)

    def _on_result(self, result: dict):
        """处理结果回调"""
        for callback in self._data_processed_callbacks:
            try:
                callback(result)
            except Exception as e:
                print(f"[DataProcessorWrapper] 回调执行失败: {e}")


# ============== 保留原有类用于兼容 ==============

class HighPerformanceBuffer:
    """高性能数据缓冲区 - 使用预分配的 numpy 数组"""

    def __init__(self, max_size: int = 50000):
        self.max_size = max_size
        self._size = 0
        self._timestamps = np.zeros(max_size, dtype=np.float64)
        self._states = []
        self._write_pos = 0
        self._is_full = False
        self._lock = threading.Lock()

    def append(self, timestamp: float, states: dict):
        """添加数据点（线程安全）"""
        with self._lock:
            self._timestamps[self._write_pos] = timestamp

            if self._is_full:
                # 覆盖旧数据
                idx = self._write_pos
                if idx < len(self._states):
                    self._states[idx] = states
                else:
                    self._states.append(states)
            else:
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
        """获取最近 n 个数据点（线程安全）"""
        with self._lock:
            if self._size == 0:
                return np.array([]), []

            if n is None or n > self._size:
                n = self._size

            if self._is_full:
                if self._write_pos >= n:
                    timestamps = self._timestamps[self._write_pos - n:self._write_pos].copy()
                    states = self._states[self._write_pos - n:self._write_pos]
                else:
                    part1_ts = self._timestamps[self.max_size - (n - self._write_pos):]
                    part2_ts = self._timestamps[:self._write_pos]
                    timestamps = np.concatenate([part1_ts, part2_ts])

                    part1_st = self._states[self.max_size - (n - self._write_pos):]
                    part2_st = self._states[:self._write_pos]
                    states = part1_st + part2_st
            else:
                start = max(0, self._write_pos - n)
                timestamps = self._timestamps[start:self._write_pos].copy()
                states = self._states[start:self._write_pos]

            return timestamps, list(states)

    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._size = 0
            self._write_pos = 0
            self._is_full = False
            self._timestamps.fill(0)
            self._states.clear()

    def __len__(self):
        return self._size


class PlotUpdateThrottler:
    """绑图更新节流器 - 限制更新频率"""

    def __init__(self, min_interval_ms: int = 33):
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
    """数据降采样器"""

    @staticmethod
    def downsample_lttb(x: np.ndarray, y: np.ndarray, target_points: int) -> tuple:
        """LTTB 降采样"""
        return _downsample_lttb_task(x, y, target_points)

    @staticmethod
    def downsample_minmax(x: np.ndarray, y: np.ndarray, target_points: int) -> tuple:
        """Min-Max 降采样"""
        n = len(x)
        if n <= target_points:
            return x, y

        bucket_size = max(1, n // (target_points // 2))
        result_x = []
        result_y = []

        for i in range(0, n, bucket_size):
            bucket_end = min(i + bucket_size, n)
            bucket_y = y[i:bucket_end]
            bucket_x = x[i:bucket_end]

            if len(bucket_y) > 0:
                min_idx = np.argmin(bucket_y)
                max_idx = np.argmax(bucket_y)

                if min_idx <= max_idx:
                    result_x.extend([bucket_x[min_idx], bucket_x[max_idx]])
                    result_y.extend([bucket_y[min_idx], bucket_y[max_idx]])
                else:
                    result_x.extend([bucket_x[max_idx], bucket_x[min_idx]])
                    result_y.extend([bucket_y[max_idx], bucket_y[min_idx]])

        return np.array(result_x), np.array(result_y)
