/**
 * Control System Box - 控制系统实时分析工具
 * C++ Qt6 + Vulkan 版本
 *
 * main.cpp - 程序入口
 *
 * 双进程架构：
 *   主进程：UI渲染（Vulkan GPU加速）
 *   计算进程：数据处理和分析任务（通过 --worker 参数启动）
 */

#include <QApplication>
#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFont>
#include <QIcon>
#include <QPixmap>
#include <QSplashScreen>
#include <QTimer>

#include "core/ComputeWorker.h"
#include "ui/MainWindow.h"

/**
 * @brief 获取资源文件路径
 * @param relativePath 相对路径
 * @return 完整路径
 */
QString getResourcePath(const QString &relativePath) {
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

/**
 * @brief 运行计算工作进程
 */
int runWorkerProcess(int argc, char *argv[], const QString &serverName) {
  QCoreApplication app(argc, argv);

  ComputeWorkerProcess worker(serverName);
  if (!worker.connectToServer()) {
    return 1;
  }
  worker.run();

  return app.exec();
}

/**
 * @brief 运行主GUI进程
 */
int runMainProcess(int argc, char *argv[]) {
  // 启用高 DPI 缩放
  QApplication::setHighDpiScaleFactorRoundingPolicy(
      Qt::HighDpiScaleFactorRoundingPolicy::PassThrough);

  QApplication app(argc, argv);

  // 设置应用程序风格
  app.setStyle("Fusion");

  // 设置应用程序信息
  app.setApplicationName("控制系统分析工具");
  app.setApplicationVersion("2.3.0");
  app.setOrganizationName("ControlSystemBox");

  // 设置应用图标
  QString iconPath = getResourcePath("images/icon.ico");
  if (QFile::exists(iconPath)) {
    app.setWindowIcon(QIcon(iconPath));
  } else {
    iconPath = getResourcePath("images/icon.jpg");
    if (QFile::exists(iconPath)) {
      app.setWindowIcon(QIcon(iconPath));
    }
  }

  // 显示启动画面
  QSplashScreen *splash = nullptr;
  QString splashPath = getResourcePath("images/splash.jpg");
  if (QFile::exists(splashPath)) {
    QPixmap splashPixmap(splashPath);
    splashPixmap = splashPixmap.scaled(600, 400, Qt::KeepAspectRatio,
                                       Qt::SmoothTransformation);
    splash = new QSplashScreen(splashPixmap);
    splash->setWindowFlags(Qt::WindowStaysOnTopHint | Qt::FramelessWindowHint);

    splash->setFont(QFont("Microsoft YaHei", 10));
    splash->showMessage("正在加载控制系统分析工具...",
                        Qt::AlignBottom | Qt::AlignHCenter, Qt::white);
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

      // 自动进入UDP模式
      QTimer::singleShot(500, [&window]() { window.autoStartUdpMode(); });
    });
  } else {
    window.show();
    QTimer::singleShot(500, [&window]() { window.autoStartUdpMode(); });
  }

  return app.exec();
}

int main(int argc, char *argv[]) {
  // 检查是否以工作进程模式启动
  QString serverName;
  bool isWorker = false;

  for (int i = 1; i < argc; ++i) {
    QString arg = QString(argv[i]);
    if (arg == "--worker" && i + 1 < argc) {
      isWorker = true;
      serverName = QString(argv[i + 1]);
      break;
    }
  }

  if (isWorker && !serverName.isEmpty()) {
    return runWorkerProcess(argc, argv, serverName);
  }

  // 运行主GUI进程
  return runMainProcess(argc, argv);
}
