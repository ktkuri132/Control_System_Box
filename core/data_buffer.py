"""
数据缓冲区模块
管理实时数据的存储和访问
"""
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class DataBuffer:
    """环形数据缓冲区"""
    max_size: int = 10000  # 最大存储点数
    
    # 使用 deque 作为环形缓冲区
    timestamps: deque = field(default_factory=lambda: deque(maxlen=10000))
    setpoints: deque = field(default_factory=lambda: deque(maxlen=10000))
    process_values: deque = field(default_factory=lambda: deque(maxlen=10000))
    control_outputs: deque = field(default_factory=lambda: deque(maxlen=10000))
    errors: deque = field(default_factory=lambda: deque(maxlen=10000))
    
    def __post_init__(self):
        # 重新初始化 deque 以使用正确的 maxlen
        self.timestamps = deque(maxlen=self.max_size)
        self.setpoints = deque(maxlen=self.max_size)
        self.process_values = deque(maxlen=self.max_size)
        self.control_outputs = deque(maxlen=self.max_size)
        self.errors = deque(maxlen=self.max_size)
    
    def append(self, timestamp: float, sp: float, pv: float, out: float, error: float):
        """添加一个数据点"""
        self.timestamps.append(timestamp)
        self.setpoints.append(sp)
        self.process_values.append(pv)
        self.control_outputs.append(out)
        self.errors.append(error)
    
    def clear(self):
        """清空所有数据"""
        self.timestamps.clear()
        self.setpoints.clear()
        self.process_values.clear()
        self.control_outputs.clear()
        self.errors.clear()
    
    def get_arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """获取 numpy 数组形式的数据"""
        return (
            np.array(self.timestamps),
            np.array(self.setpoints),
            np.array(self.process_values),
            np.array(self.control_outputs),
            np.array(self.errors)
        )
    
    def get_latest(self, n: int = 1000) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """获取最近 n 个数据点"""
        t, sp, pv, out, err = self.get_arrays()
        if len(t) > n:
            return t[-n:], sp[-n:], pv[-n:], out[-n:], err[-n:]
        return t, sp, pv, out, err
    
    def __len__(self) -> int:
        return len(self.timestamps)


class DataManager(QObject):
    """数据管理器，负责数据的收集和分发"""
    data_updated = pyqtSignal()  # 数据更新信号
    
    def __init__(self, buffer_size: int = 10000):
        super().__init__()
        self.buffer = DataBuffer(max_size=buffer_size)
        self._update_counter = 0
        self._update_interval = 1  # 每收到几个点发送一次更新信号
    
    def add_data(self, timestamp: float, sp: float, pv: float, out: float, error: float):
        """添加数据点"""
        self.buffer.append(timestamp, sp, pv, out, error)
        self._update_counter += 1
        
        # 节流：不是每个数据点都触发更新
        if self._update_counter >= self._update_interval:
            self._update_counter = 0
            self.data_updated.emit()
    
    def set_update_interval(self, interval: int):
        """设置更新间隔"""
        self._update_interval = max(1, interval)
    
    def clear(self):
        """清空数据"""
        self.buffer.clear()
        self.data_updated.emit()
    
    def get_data(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """获取所有数据"""
        return self.buffer.get_arrays()
    
    def get_latest_data(self, n: int = 1000) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """获取最近的数据"""
        return self.buffer.get_latest(n)
