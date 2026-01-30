"""
模拟数据生成器
用于测试和演示，无需真实硬件
"""
import math
import random
import time
from PyQt6.QtCore import QThread, pyqtSignal


class SimulatedSerialWorker(QThread):
    """模拟串口数据发送器"""
    data_generated = pyqtSignal(str)
    
    def __init__(self, sample_rate: int = 100):
        super().__init__()
        self._running = False
        self._sample_rate = sample_rate
        self._interval = 1.0 / sample_rate
        
        # 模拟系统参数
        self._setpoint = 50.0
        self._process_value = 0.0
        self._output = 0.0
        
        # 简单的一阶系统模型
        self._time_constant = 0.5  # 时间常数
        self._gain = 1.0
        self._noise_level = 0.5
        
        # PID参数（模拟）
        self._kp = 1.0
        self._ki = 0.1
        self._kd = 0.05
        self._integral = 0.0
        self._last_error = 0.0
    
    def run(self):
        self._running = True
        self._start_time = time.time()
        
        while self._running:
            # 计算误差
            error = self._setpoint - self._process_value
            
            # PID计算
            self._integral += error * self._interval
            derivative = (error - self._last_error) / self._interval
            
            self._output = (
                self._kp * error +
                self._ki * self._integral +
                self._kd * derivative
            )
            
            # 限制输出范围
            self._output = max(0, min(100, self._output))
            
            self._last_error = error
            
            # 一阶系统响应
            alpha = self._interval / (self._time_constant + self._interval)
            target = self._gain * self._output
            self._process_value = (1 - alpha) * self._process_value + alpha * target
            
            # 添加噪声
            self._process_value += random.gauss(0, self._noise_level)
            
            # 生成数据字符串
            data_line = f"SP:{self._setpoint:.2f},PV:{self._process_value:.2f},OUT:{self._output:.2f}"
            self.data_generated.emit(data_line)
            
            # 按采样率休眠
            self.msleep(int(self._interval * 1000))
    
    def stop(self):
        self._running = False
        self.wait(1000)
    
    def set_setpoint(self, sp: float):
        self._setpoint = sp
    
    def set_pid(self, kp: float, ki: float, kd: float):
        self._kp = kp
        self._ki = ki
        self._kd = kd
        # 重置积分项，避免积分饱和
        self._integral = 0.0


class DemoDataGenerator:
    """
    演示数据生成器
    生成各种典型的控制系统响应
    """
    
    @staticmethod
    def step_response(t: float, final_value: float = 100.0, 
                      time_constant: float = 1.0, damping: float = 0.7) -> float:
        """
        生成二阶系统阶跃响应
        
        Args:
            t: 时间
            final_value: 最终稳态值
            time_constant: 时间常数
            damping: 阻尼比 (0-1: 欠阻尼, 1: 临界阻尼, >1: 过阻尼)
        """
        if t < 0:
            return 0.0
        
        omega_n = 1.0 / time_constant  # 自然频率
        
        if damping < 1:  # 欠阻尼
            omega_d = omega_n * math.sqrt(1 - damping**2)
            response = 1 - math.exp(-damping * omega_n * t) * (
                math.cos(omega_d * t) + 
                (damping / math.sqrt(1 - damping**2)) * math.sin(omega_d * t)
            )
        elif damping == 1:  # 临界阻尼
            response = 1 - (1 + omega_n * t) * math.exp(-omega_n * t)
        else:  # 过阻尼
            s1 = -omega_n * (damping - math.sqrt(damping**2 - 1))
            s2 = -omega_n * (damping + math.sqrt(damping**2 - 1))
            response = 1 + (s1 * math.exp(s2 * t) - s2 * math.exp(s1 * t)) / (s2 - s1)
        
        return final_value * response
    
    @staticmethod
    def sine_wave(t: float, amplitude: float = 10.0, frequency: float = 0.5,
                  offset: float = 50.0) -> float:
        """生成正弦波"""
        return offset + amplitude * math.sin(2 * math.pi * frequency * t)
    
    @staticmethod
    def add_noise(value: float, noise_std: float = 0.5) -> float:
        """添加高斯噪声"""
        return value + random.gauss(0, noise_std)
