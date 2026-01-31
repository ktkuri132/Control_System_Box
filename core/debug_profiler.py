"""
调试性能分析模块
仅在调试模式下启用，不影响发行版性能

使用方法：
1. 设置环境变量 DEBUG_MODE=1 启用调试模式
2. 或者使用 python -O main.py 禁用调试模式（__debug__=False）

功能：
- CPU 核心利用率监控
- 进程 CPU 使用率监控
- 函数耗时统计
- 内存使用监控
- 性能瓶颈分析
"""
import os
import sys
import time
import threading
import functools
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from dataclasses import dataclass, field
import multiprocessing as mp

# ============== 调试模式检测 ==============

# 方式1：通过环境变量控制
DEBUG_MODE = os.environ.get('DEBUG_MODE', '0') == '1'

# 方式2：通过 Python 的 __debug__ 变量（python -O 禁用）
# DEBUG_MODE = __debug__

# 方式3：通过配置文件
# DEBUG_MODE = read_config('debug_mode', False)

if DEBUG_MODE:
    print("[DebugProfiler] 调试模式: 启用", flush=True)
else:
    print("[DebugProfiler] 调试模式: 禁用", flush=True)


# ============== 性能数据结构 ==============

@dataclass
class FunctionStats:
    """函数统计数据"""
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    recent_times: List[float] = field(default_factory=list)

    def add_sample(self, duration: float):
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.recent_times.append(duration)
        if len(self.recent_times) > 100:
            self.recent_times.pop(0)

    @property
    def avg_time(self) -> float:
        return self.total_time / max(1, self.call_count)

    @property
    def recent_avg(self) -> float:
        if not self.recent_times:
            return 0.0
        return sum(self.recent_times) / len(self.recent_times)


@dataclass
class CPUStats:
    """CPU 统计数据"""
    core_count: int = 0
    per_core_percent: List[float] = field(default_factory=list)
    process_percent: float = 0.0
    process_threads: int = 0
    timestamp: float = 0.0


# ============== 性能分析器 ==============

class PerformanceProfiler:
    """
    性能分析器
    收集和报告各种性能指标
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._function_stats: Dict[str, FunctionStats] = defaultdict(FunctionStats)
        self._cpu_history: List[CPUStats] = []
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

        # 尝试导入 psutil（可选依赖）
        self._psutil = None
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            print("[DebugProfiler] 警告: psutil 未安装，CPU 监控功能受限")
            print("[DebugProfiler] 安装: pip install psutil")

    def start_monitoring(self, interval: float = 1.0):
        """启动后台 CPU 监控"""
        if not DEBUG_MODE:
            return

        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        print(f"[DebugProfiler] CPU 监控已启动，间隔 {interval}s")

    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._running:
            stats = self._collect_cpu_stats()
            if stats:
                with self._lock:
                    self._cpu_history.append(stats)
                    # 只保留最近 60 个样本
                    if len(self._cpu_history) > 60:
                        self._cpu_history.pop(0)
            time.sleep(interval)

    def _collect_cpu_stats(self) -> Optional[CPUStats]:
        """收集 CPU 统计"""
        if not self._psutil:
            return None

        try:
            stats = CPUStats()
            stats.timestamp = time.time()
            stats.core_count = mp.cpu_count()
            stats.per_core_percent = self._psutil.cpu_percent(percpu=True)

            process = self._psutil.Process()
            stats.process_percent = process.cpu_percent()
            stats.process_threads = process.num_threads()

            return stats
        except Exception as e:
            print(f"[DebugProfiler] 收集 CPU 统计失败: {e}")
            return None

    def record_function_time(self, func_name: str, duration: float):
        """记录函数执行时间"""
        if not DEBUG_MODE:
            return

        with self._lock:
            self._function_stats[func_name].add_sample(duration)

    def get_function_stats(self) -> Dict[str, FunctionStats]:
        """获取函数统计"""
        with self._lock:
            return dict(self._function_stats)

    def get_latest_cpu_stats(self) -> Optional[CPUStats]:
        """获取最新的 CPU 统计"""
        with self._lock:
            if self._cpu_history:
                return self._cpu_history[-1]
            return None

    def get_cpu_history(self) -> List[CPUStats]:
        """获取 CPU 历史"""
        with self._lock:
            return list(self._cpu_history)

    def print_report(self):
        """打印性能报告"""
        if not DEBUG_MODE:
            return

        import sys

        print("\n" + "=" * 60, flush=True)
        print("                   性能分析报告", flush=True)
        print("=" * 60, flush=True)

        # CPU 统计
        cpu_stats = self.get_latest_cpu_stats()
        if cpu_stats:
            print(f"\n【CPU 状态】", flush=True)
            print(f"  核心数: {cpu_stats.core_count}", flush=True)
            print(f"  进程 CPU 使用率: {cpu_stats.process_percent:.1f}%", flush=True)
            print(f"  进程线程数: {cpu_stats.process_threads}", flush=True)
            print(f"  各核心使用率:", flush=True)
            for i, pct in enumerate(cpu_stats.per_core_percent):
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"    核心 {i:2d}: [{bar}] {pct:5.1f}%", flush=True)

        # 函数统计
        func_stats = self.get_function_stats()
        if func_stats:
            print(f"\n【函数耗时统计】(按总时间排序)", flush=True)
            sorted_stats = sorted(
                func_stats.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )
            print(f"  {'函数名':<40} {'调用次数':>10} {'平均(ms)':>10} {'最大(ms)':>10}", flush=True)
            print(f"  {'-' * 40} {'-' * 10} {'-' * 10} {'-' * 10}", flush=True)
            for name, stats in sorted_stats[:20]:
                print(f"  {name:<40} {stats.call_count:>10} "
                      f"{stats.avg_time*1000:>10.2f} {stats.max_time*1000:>10.2f}")

        print("\n" + "=" * 60)

    def get_bottleneck_analysis(self) -> str:
        """分析性能瓶颈"""
        if not DEBUG_MODE:
            return "调试模式未启用"

        analysis = []

        # 分析 CPU 使用情况
        cpu_stats = self.get_latest_cpu_stats()
        if cpu_stats:
            avg_core_usage = sum(cpu_stats.per_core_percent) / len(cpu_stats.per_core_percent)
            max_core_usage = max(cpu_stats.per_core_percent)

            if cpu_stats.process_percent < 50 and avg_core_usage < 30:
                analysis.append("⚠️ CPU 利用率低，可能存在 I/O 等待或锁竞争")

            if max_core_usage > 90 and avg_core_usage < 50:
                analysis.append("⚠️ 单核负载高但整体 CPU 利用率低，可能是 GIL 瓶颈")
                analysis.append("   建议：使用多进程代替多线程处理 CPU 密集型任务")

            if cpu_stats.process_percent > 150:  # 超过 100% 表示多核
                analysis.append("✅ 多核利用良好")

        # 分析函数耗时
        func_stats = self.get_function_stats()
        if func_stats:
            sorted_stats = sorted(
                func_stats.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )
            if sorted_stats:
                top_func, top_stats = sorted_stats[0]
                if top_stats.avg_time > 0.1:  # 平均耗时超过 100ms
                    analysis.append(f"⚠️ 函数 '{top_func}' 平均耗时 {top_stats.avg_time*1000:.1f}ms，可能是瓶颈")

        if not analysis:
            analysis.append("✅ 未检测到明显的性能瓶颈")

        return "\n".join(analysis)


# ============== 装饰器 ==============

def profile_function(func: Callable) -> Callable:
    """
    函数性能分析装饰器
    仅在调试模式下记录执行时间

    用法：
        @profile_function
        def my_function():
            ...
    """
    if not DEBUG_MODE:
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            profiler = PerformanceProfiler()
            profiler.record_function_time(func.__qualname__, duration)

    return wrapper


def profile_method(func: Callable) -> Callable:
    """
    方法性能分析装饰器（包含类名）
    """
    if not DEBUG_MODE:
        return func

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        try:
            return func(self, *args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            profiler = PerformanceProfiler()
            func_name = f"{self.__class__.__name__}.{func.__name__}"
            profiler.record_function_time(func_name, duration)

    return wrapper


class ProfileBlock:
    """
    代码块性能分析上下文管理器

    用法：
        with ProfileBlock("数据处理"):
            # 耗时代码
            ...
    """
    def __init__(self, name: str):
        self.name = name
        self.start = 0

    def __enter__(self):
        if DEBUG_MODE:
            self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        if DEBUG_MODE:
            duration = time.perf_counter() - self.start
            profiler = PerformanceProfiler()
            profiler.record_function_time(f"Block:{self.name}", duration)


# ============== 便捷函数 ==============

def debug_print(*args, **kwargs):
    """调试打印，仅在调试模式下输出"""
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)


def start_profiling():
    """启动性能分析"""
    if DEBUG_MODE:
        profiler = PerformanceProfiler()
        profiler.start_monitoring(interval=1.0)


def stop_profiling():
    """停止性能分析"""
    if DEBUG_MODE:
        profiler = PerformanceProfiler()
        profiler.stop_monitoring()


def print_performance_report():
    """打印性能报告"""
    if DEBUG_MODE:
        profiler = PerformanceProfiler()
        profiler.print_report()


def get_profiler() -> PerformanceProfiler:
    """获取性能分析器实例"""
    return PerformanceProfiler()


# ============== 实时性能面板（可选）==============

class PerformancePanel:
    """
    实时性能面板
    可以集成到 PyQt6 界面中
    """
    def __init__(self):
        self._profiler = PerformanceProfiler()

    def get_display_text(self) -> str:
        """获取显示文本"""
        if not DEBUG_MODE:
            return "调试模式未启用"

        lines = ["=== 实时性能监控 ==="]

        cpu_stats = self._profiler.get_latest_cpu_stats()
        if cpu_stats:
            lines.append(f"进程 CPU: {cpu_stats.process_percent:.1f}%")
            lines.append(f"线程数: {cpu_stats.process_threads}")

            # 核心使用率条形图
            for i, pct in enumerate(cpu_stats.per_core_percent[:8]):  # 最多显示 8 核
                bar = "█" * int(pct / 10)
                lines.append(f"Core {i}: {bar} {pct:.0f}%")

        # 最耗时的函数
        func_stats = self._profiler.get_function_stats()
        if func_stats:
            sorted_stats = sorted(
                func_stats.items(),
                key=lambda x: x[1].recent_avg,
                reverse=True
            )[:5]
            if sorted_stats:
                lines.append("\n--- 耗时函数 TOP5 ---")
                for name, stats in sorted_stats:
                    short_name = name.split('.')[-1][:20]
                    lines.append(f"{short_name}: {stats.recent_avg*1000:.1f}ms")

        return "\n".join(lines)
