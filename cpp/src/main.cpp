/**
 * Control System Box - 控制系统实时分析工具
 * C++ Qt6 版本
 *
 * main.cpp - 程序入口
 */

#include <QApplication>
#include <QSplashScreen>
#include <QTimer>
#include <QPixmap>
#include <QIcon>
#include <QFont>
#include <QDir>
#include <QFile>

#include "ui/MainWindow.h"

/**
 * @brief 获取资源文件路径
 * @param relativePath 相对路径
 * @return 完整路径
 */
QString getResourcePath(const QString& relativePath) {
    // 首先检查可执行文件同级目录
    QString exeDir = QCoreApplication::applicationDirPath();
    QString path = exeDir + "/" + relativePath;
    if (QFile::exists(path)) {
        return path;
    }

    // 开发环境路径
    path = QDir::currentPath() + "/resources/" + relativePath;
    if (QFile::exists(path)) {
        return path;
    }

    // 使用资源文件系统
    return ":/" + relativePath;
}

int main(int argc, char *argv[]) {
    // 启用高 DPI 缩放
    QApplication::setHighDpiScaleFactorRoundingPolicy(
        Qt::HighDpiScaleFactorRoundingPolicy::PassThrough
    );

    QApplication app(argc, argv);

    // 设置应用程序风格
    app.setStyle("Fusion");

    // 设置应用程序信息
    app.setApplicationName("控制系统分析工具");
    app.setApplicationVersion("2.1.2");
    app.setOrganizationName("ControlSystemBox");

    // 设置应用图标
    QString iconPath = getResourcePath("images/icon.ico");
    if (QFile::exists(iconPath)) {
        app.setWindowIcon(QIcon(iconPath));
    } else {
        // 尝试 jpg 格式
        iconPath = getResourcePath("images/icon.jpg");
        if (QFile::exists(iconPath)) {
            app.setWindowIcon(QIcon(iconPath));
        }
    }

    // 显示启动画面
    QSplashScreen* splash = nullptr;
    QString splashPath = getResourcePath("images/splash.jpg");
    if (QFile::exists(splashPath)) {
        QPixmap splashPixmap(splashPath);
        // 缩放启动图到合适大小
        splashPixmap = splashPixmap.scaled(
            600, 400,
            Qt::KeepAspectRatio,
            Qt::SmoothTransformation
        );
        splash = new QSplashScreen(splashPixmap);
        splash->setWindowFlags(Qt::WindowStaysOnTopHint | Qt::FramelessWindowHint);

        // 设置启动画面文字样式
        splash->setFont(QFont("Microsoft YaHei", 10));
        splash->showMessage(
            "正在加载控制系统分析工具...",
            Qt::AlignBottom | Qt::AlignHCenter,
            Qt::white
        );
        splash->show();
        app.processEvents();
    }

    // 创建主窗口
    MainWindow window;

    // 关闭启动画面并显示主窗口
    if (splash) {
        QTimer::singleShot(1500, [splash, &window]() {
            splash->finish(&window);
            window.show();
            delete splash;
        });
    } else {
        window.show();
    }

    return app.exec();
}
