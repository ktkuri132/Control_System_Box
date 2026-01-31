"""
自动控制系统实时辅助分析工具
主入口文件
"""
import sys
import os
import multiprocessing

# Windows 多进程支持：必须在最开始调用
if __name__ == "__main__":
    multiprocessing.freeze_support()

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont


def get_resource_path(relative_path):
    """获取资源文件路径，支持打包后的路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 风格，跨平台一致性好
    
    # 设置应用程序信息
    app.setApplicationName("控制系统分析工具")
    app.setApplicationVersion("2.1.2")
    app.setOrganizationName("ControlSystemBox")
    
    # 设置应用图标
    icon_path = get_resource_path("img/icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        # 尝试 jpg 格式
        icon_path = get_resource_path("img/icon.jpg")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

    # 显示启动画面
    splash = None
    splash_path = get_resource_path("img/strat.jpg")
    if os.path.exists(splash_path):
        splash_pixmap = QPixmap(splash_path)
        # 缩放启动图到合适大小
        splash_pixmap = splash_pixmap.scaled(
            600, 400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        splash = QSplashScreen(splash_pixmap)
        splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

        # 设置启动画面文字样式
        splash.setFont(QFont("Microsoft YaHei", 10))
        splash.showMessage(
            "正在加载控制系统分析工具...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            Qt.GlobalColor.white
        )
        splash.show()
        app.processEvents()

    # 导入主窗口（放在启动画面之后，这样加载时会显示启动画面）
    from ui.main_window import MainWindow

    window = MainWindow()

    # 关闭启动画面并显示主窗口
    if splash:
        QTimer.singleShot(1500, lambda: (splash.finish(window), window.show()))
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
