"""
自动化性能测试脚本
运行程序1分钟，收集性能数据，然后导出报告
"""
import os
import sys
import time
import json
import threading
from datetime import datetime

# 设置调试模式
os.environ['DEBUG_MODE'] = '1'

# 导入性能分析器
from core.debug_profiler import (
    DEBUG_MODE, get_profiler, start_profiling, stop_profiling
)

# 测试配置
TEST_DURATION_SECONDS = 60  # 测试持续时间
REPORT_FILE = "performance_report.txt"
REPORT_JSON = "performance_data.json"


class AutoPerformanceTest:
    """自动化性能测试"""

    def __init__(self, duration: int = 60):
        self.duration = duration
        self.profiler = get_profiler()
        self.start_time = None
        self.collected_data = []
        self._running = False

    def start(self):
        """启动测试"""
        print(f"\n{'='*60}")
        print(f"   自动化性能测试")
        print(f"   测试时长: {self.duration} 秒")
        print(f"{'='*60}\n")

        self.start_time = time.time()
        self._running = True

        # 启动性能监控
        start_profiling()

        # 启动数据收集线程
        self._collector_thread = threading.Thread(target=self._collect_data, daemon=True)
        self._collector_thread.start()

        # 启动倒计时线程
        self._countdown_thread = threading.Thread(target=self._countdown, daemon=True)
        self._countdown_thread.start()

    def _countdown(self):
        """倒计时显示"""
        while self._running:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.duration - elapsed)

            if remaining <= 0:
                break

            # 每10秒打印一次
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"[测试进度] 已运行 {int(elapsed)}s, 剩余 {int(remaining)}s", flush=True)

            time.sleep(1)

    def _collect_data(self):
        """收集性能数据"""
        while self._running:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                break

            # 每秒收集一次数据
            cpu_stats = self.profiler.get_latest_cpu_stats()
            if cpu_stats:
                self.collected_data.append({
                    'timestamp': elapsed,
                    'process_cpu': cpu_stats.process_percent,
                    'process_threads': cpu_stats.process_threads,
                    'per_core_percent': list(cpu_stats.per_core_percent),
                    'core_count': cpu_stats.core_count
                })

            time.sleep(1)

    def should_stop(self) -> bool:
        """检查是否应该停止"""
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.duration

    def stop_and_report(self):
        """停止并生成报告"""
        self._running = False
        stop_profiling()

        print(f"\n{'='*60}")
        print("   测试完成，正在生成报告...")
        print(f"{'='*60}\n")

        # 生成文本报告
        self._generate_text_report()

        # 生成 JSON 数据
        self._generate_json_report()

        print(f"\n报告已生成:")
        print(f"  - {REPORT_FILE}")
        print(f"  - {REPORT_JSON}")

    def _generate_text_report(self):
        """生成文本报告"""
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("              控制系统分析工具 - 性能测试报告\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试时长: {self.duration} 秒\n")
            f.write(f"采样点数: {len(self.collected_data)}\n\n")

            # CPU 统计摘要
            if self.collected_data:
                f.write("-" * 70 + "\n")
                f.write("【CPU 使用率统计】\n")
                f.write("-" * 70 + "\n\n")

                process_cpus = [d['process_cpu'] for d in self.collected_data]
                core_count = self.collected_data[0]['core_count']

                f.write(f"CPU 核心数: {core_count}\n")
                f.write(f"进程 CPU 使用率:\n")
                f.write(f"  - 平均: {sum(process_cpus)/len(process_cpus):.1f}%\n")
                f.write(f"  - 最大: {max(process_cpus):.1f}%\n")
                f.write(f"  - 最小: {min(process_cpus):.1f}%\n\n")

                # 各核心统计
                f.write("各核心 CPU 使用率:\n")
                for i in range(core_count):
                    core_usages = [d['per_core_percent'][i] for d in self.collected_data if i < len(d['per_core_percent'])]
                    if core_usages:
                        avg = sum(core_usages) / len(core_usages)
                        bar = "█" * int(avg / 5) + "░" * (20 - int(avg / 5))
                        f.write(f"  核心 {i:2d}: [{bar}] 平均 {avg:5.1f}%  最大 {max(core_usages):5.1f}%\n")

                f.write("\n")

            # 函数耗时统计
            f.write("-" * 70 + "\n")
            f.write("【函数耗时统计】\n")
            f.write("-" * 70 + "\n\n")

            func_stats = self.profiler.get_function_stats()
            if func_stats:
                sorted_stats = sorted(
                    func_stats.items(),
                    key=lambda x: x[1].total_time,
                    reverse=True
                )

                f.write(f"{'函数名':<45} {'调用次数':>10} {'平均(ms)':>12} {'最大(ms)':>12} {'总时间(s)':>12}\n")
                f.write("-" * 95 + "\n")

                for name, stats in sorted_stats[:30]:
                    f.write(f"{name:<45} {stats.call_count:>10} "
                           f"{stats.avg_time*1000:>12.2f} {stats.max_time*1000:>12.2f} "
                           f"{stats.total_time:>12.3f}\n")
            else:
                f.write("无函数耗时数据\n")

            f.write("\n")

            # 瓶颈分析
            f.write("-" * 70 + "\n")
            f.write("【性能瓶颈分析】\n")
            f.write("-" * 70 + "\n\n")

            f.write(self._analyze_bottlenecks())

            f.write("\n" + "=" * 70 + "\n")
            f.write("                         报告结束\n")
            f.write("=" * 70 + "\n")

    def _analyze_bottlenecks(self) -> str:
        """分析性能瓶颈"""
        analysis = []

        if not self.collected_data:
            return "无数据可分析\n"

        # 计算统计数据
        process_cpus = [d['process_cpu'] for d in self.collected_data]
        avg_process_cpu = sum(process_cpus) / len(process_cpus)
        max_process_cpu = max(process_cpus)
        core_count = self.collected_data[0]['core_count']

        # 计算各核心平均使用率
        core_avgs = []
        for i in range(core_count):
            core_usages = [d['per_core_percent'][i] for d in self.collected_data if i < len(d['per_core_percent'])]
            if core_usages:
                core_avgs.append(sum(core_usages) / len(core_usages))

        overall_avg = sum(core_avgs) / len(core_avgs) if core_avgs else 0
        max_core_avg = max(core_avgs) if core_avgs else 0

        # 分析1: 进程 CPU 利用率
        analysis.append(f"1. 进程 CPU 利用率分析:")
        analysis.append(f"   - 平均使用率: {avg_process_cpu:.1f}%")
        analysis.append(f"   - 最大使用率: {max_process_cpu:.1f}%")

        # 理论最大值是 100% * 核心数
        max_theoretical = 100 * core_count
        utilization_ratio = avg_process_cpu / max_theoretical * 100
        analysis.append(f"   - CPU 利用效率: {utilization_ratio:.1f}% (相对于 {core_count} 核)")

        if avg_process_cpu < 100:
            analysis.append(f"   ⚠️ 进程平均 CPU 使用率低于 100%，可能存在:")
            analysis.append(f"      - I/O 等待")
            analysis.append(f"      - 线程阻塞/锁竞争")
            analysis.append(f"      - GIL 限制（如果是单线程 CPU 密集型）")
        elif avg_process_cpu > 100 and avg_process_cpu < 200:
            analysis.append(f"   ✓ 进程使用了约 1-2 个核心的计算资源")
        elif avg_process_cpu >= 200:
            analysis.append(f"   ✓ 多核利用良好，使用了约 {avg_process_cpu/100:.1f} 个核心")

        analysis.append("")

        # 分析2: 核心负载均衡
        analysis.append(f"2. CPU 核心负载均衡分析:")
        analysis.append(f"   - 整体平均使用率: {overall_avg:.1f}%")
        analysis.append(f"   - 最高核心平均使用率: {max_core_avg:.1f}%")

        load_imbalance = max_core_avg - overall_avg
        if load_imbalance > 20:
            analysis.append(f"   ⚠️ 核心负载不均衡 (差异: {load_imbalance:.1f}%)")
            analysis.append(f"      可能原因: 单线程瓶颈或 GIL 限制")
        else:
            analysis.append(f"   ✓ 核心负载相对均衡")

        analysis.append("")

        # 分析3: GIL 瓶颈检测
        analysis.append(f"3. Python GIL 瓶颈检测:")

        # 如果单核使用率高但进程整体使用率不高，可能是 GIL 问题
        if max_core_avg > 80 and avg_process_cpu < 150:
            analysis.append(f"   ⚠️ 疑似 GIL 瓶颈!")
            analysis.append(f"      - 单核负载高 ({max_core_avg:.1f}%)")
            analysis.append(f"      - 但进程整体 CPU 使用率低 ({avg_process_cpu:.1f}%)")
            analysis.append(f"      建议: 将 CPU 密集型计算移至多进程")
        else:
            analysis.append(f"   ✓ 未检测到明显的 GIL 瓶颈")

        analysis.append("")

        # 分析4: 函数耗时分析
        analysis.append(f"4. 热点函数分析:")
        func_stats = self.profiler.get_function_stats()
        if func_stats:
            sorted_stats = sorted(
                func_stats.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )[:5]

            total_time = sum(s[1].total_time for s in sorted_stats)
            if total_time > 0:
                for name, stats in sorted_stats:
                    pct = stats.total_time / total_time * 100
                    if stats.avg_time > 0.05:  # 平均耗时超过 50ms
                        analysis.append(f"   ⚠️ {name}")
                        analysis.append(f"      平均耗时: {stats.avg_time*1000:.1f}ms, 占比: {pct:.1f}%")
                    else:
                        analysis.append(f"   ✓ {name}: 平均 {stats.avg_time*1000:.1f}ms")
        else:
            analysis.append(f"   无函数耗时数据")

        analysis.append("")

        # 总结建议
        analysis.append("=" * 50)
        analysis.append("【优化建议】")
        analysis.append("=" * 50)

        suggestions = []

        if avg_process_cpu < 100 and max_core_avg > 50:
            suggestions.append("1. 考虑使用多进程 (multiprocessing) 代替多线程处理 CPU 密集型任务")

        if max_core_avg > 80 and avg_process_cpu < 150:
            suggestions.append("2. 当前代码可能受 Python GIL 限制，建议将数据处理移至独立进程")

        if func_stats:
            slow_funcs = [name for name, stats in func_stats.items() if stats.avg_time > 0.1]
            if slow_funcs:
                suggestions.append(f"3. 以下函数耗时较长，建议优化: {', '.join(slow_funcs[:3])}")

        if not suggestions:
            suggestions.append("当前性能表现良好，无明显瓶颈")

        for s in suggestions:
            analysis.append(f"   {s}")

        return "\n".join(analysis)

    def _generate_json_report(self):
        """生成 JSON 格式报告"""
        func_stats = self.profiler.get_function_stats()
        func_data = {}
        for name, stats in func_stats.items():
            func_data[name] = {
                'call_count': stats.call_count,
                'total_time': stats.total_time,
                'avg_time': stats.avg_time,
                'min_time': stats.min_time,
                'max_time': stats.max_time
            }

        report = {
            'test_time': datetime.now().isoformat(),
            'duration': self.duration,
            'sample_count': len(self.collected_data),
            'cpu_samples': self.collected_data,
            'function_stats': func_data
        }

        with open(REPORT_JSON, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


# 全局测试实例
_test_instance = None


def get_test_instance() -> AutoPerformanceTest:
    global _test_instance
    if _test_instance is None:
        _test_instance = AutoPerformanceTest(TEST_DURATION_SECONDS)
    return _test_instance


def check_and_stop(window):
    """检查是否应该停止测试"""
    test = get_test_instance()
    if test.should_stop():
        test.stop_and_report()
        window.close()
        return True
    return False


# 如果直接运行此脚本，启动完整测试
if __name__ == "__main__":
    print("请使用 run_perf_test.bat 运行性能测试")
