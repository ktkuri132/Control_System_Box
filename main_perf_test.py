"""
自动控制系统实时辅助分析工具
性能测试入口文件 - 自动运行1分钟后停止并生成报告
"""
import sys
import os
import multiprocessing

# 设置调试模式和性能测试模式
os.environ['DEBUG_MODE'] = '1'
os.environ['PERF_TEST_MODE'] = '1'

# Windows 多进程支持：必须在最开始调用
if __name__ == "__main__":
    multiprocessing.freeze_support()

from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont

# 导入性能测试模块
from auto_perf_test import get_test_instance, check_and_stop


def get_resource_path(relative_path):
    """获取资源文件路径，支持打包后的路径"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用程序信息
    app.setApplicationName("控制系统分析工具 - 性能测试")
    app.setApplicationVersion("2.0.1")
    app.setOrganizationName("ControlSystemBox")

    # 设置应用图标
    icon_path = get_resource_path("img/icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 导入主窗口
    from ui.main_window import MainWindow

    window = MainWindow()
    window.setWindowTitle("控制系统分析工具 - 性能测试模式 (60秒后自动停止)")
    window.show()

    # 显示提示
    QMessageBox.information(
        window,
        "性能测试模式",
        "性能测试已启动！\n\n"
        "请执行以下步骤:\n"
        "1. 切换到「仿真数据」模式\n"
        "2. 点击「开始仿真」\n"
        "3. 程序将在 60 秒后自动停止\n"
        "4. 性能报告将保存到当前目录\n\n"
        "点击「确定」开始测试计时"
    )

    # 启动性能测试
    test = get_test_instance()
    test.start()

    # 创建检查定时器
    check_timer = QTimer()
    check_timer.timeout.connect(lambda: check_and_stop(window))
    check_timer.start(1000)  # 每秒检查一次

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
