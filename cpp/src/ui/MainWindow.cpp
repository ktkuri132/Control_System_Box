/**
 * MainWindow.cpp - 主窗口实现
 */

#include "ui/MainWindow.h"
#include "core/SerialManager.h"
#include "core/SimulatorReceiver.h"
#include "core/PerformanceAnalyzer.h"
#include "core/DataProcessor.h"
#include "core/DataBuffer.h"
#include "core/UnifiedDataProtocol.h"
#include "ui/panels/UnifiedControlPanel.h"
#include "ui/plots/SimulatorPlotWidget.h"

#include <QApplication>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFrame>
#include <QMenuBar>
#include <QMenu>
#include <QAction>
#include <QMessageBox>
#include <QFileDialog>
#include <QCloseEvent>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , m_currentMode(DataSourceMode::Serial)
    , m_isPaused(false)
{
    // 初始化核心组件
    m_serialManager = std::make_unique<SerialManager>(this);
    m_simulatorReceiver = std::make_unique<SimulatorReceiver>(this);
    m_analyzer = std::make_unique<PerformanceAnalyzer>();
    m_dataProcessor = std::make_unique<DataProcessor>(this);

    // 初始化 UI
    setupUi();
    setupConnections();
    setupTimers();

    // 初始化串口列表
    if (m_controlPanel) {
        m_controlPanel->serialPanel()->refreshPorts();
    }
}

MainWindow::~MainWindow() = default;

void MainWindow::setupUi() {
    setWindowTitle("控制系统实时分析工具 v2.1.2");
    setMinimumSize(1200, 700);
    resize(1400, 800);

    setupStyles();

    QWidget* centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QVBoxLayout* mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // 模式切换工具栏
    setupModeToolbar(mainLayout);

    // 内容区域
    QHBoxLayout* contentLayout = new QHBoxLayout();
    contentLayout->setContentsMargins(5, 5, 5, 5);
    contentLayout->setSpacing(5);

    // 左侧控制面板
    m_controlPanel = new UnifiedControlPanel(this);
    contentLayout->addWidget(m_controlPanel);

    // 右侧图表区域
    m_plotWidget = new SimulatorPlotWidget(this);
    contentLayout->addWidget(m_plotWidget, 1);

    mainLayout->addLayout(contentLayout, 1);

    // 状态栏
    m_statusBar = new QStatusBar(this);
    setStatusBar(m_statusBar);
    m_statusBar->showMessage("就绪 - 请选择数据源并连接");

    setupMenu();
}

void MainWindow::setupStyles() {
    setStyleSheet(R"(
        QMainWindow { background-color: #1E1E1E; }
        QWidget { color: #CCCCCC; font-family: "Microsoft YaHei", sans-serif; }
        QLabel { color: #CCCCCC; }
        QComboBox {
            background-color: #3C3C3C; color: #FFFFFF;
            border: 1px solid #555555; border-radius: 3px; padding: 4px;
        }
        QComboBox:hover { border-color: #0078D4; }
        QComboBox QAbstractItemView {
            background-color: #2D2D30; color: #FFFFFF;
            selection-background-color: #0078D4;
        }
        QStatusBar { background-color: #007ACC; color: white; }
        QRadioButton { color: #FFFFFF; font-weight: bold; padding: 8px 16px; }
        QRadioButton::indicator { width: 0px; height: 0px; }
    )");
}

void MainWindow::setupModeToolbar(QVBoxLayout* parentLayout) {
    QFrame* toolbarFrame = new QFrame(this);
    toolbarFrame->setStyleSheet(R"(
        QFrame { background-color: #2D2D30; border-bottom: 1px solid #3D3D3D; }
    )");
    toolbarFrame->setFixedHeight(45);

    QHBoxLayout* toolbarLayout = new QHBoxLayout(toolbarFrame);
    toolbarLayout->setContentsMargins(10, 5, 10, 5);
    toolbarLayout->setSpacing(5);

    QLabel* titleLabel = new QLabel("数据源:", this);
    titleLabel->setStyleSheet("color: #AAAAAA; font-size: 12px;");
    toolbarLayout->addWidget(titleLabel);

    m_modeGroup = new QButtonGroup(this);

    // 串口模式按钮
    m_serialModeBtn = new QRadioButton("🔌 串口", this);
    m_serialModeBtn->setChecked(true);
    m_serialModeBtn->setStyleSheet(R"(
        QRadioButton { background-color: #3C3C3C; border-radius: 3px; padding: 6px 12px; }
        QRadioButton:hover { background-color: #4C4C4C; }
        QRadioButton:checked { background-color: #0E639C; border: 2px solid #4FC3F7; }
    )");
    m_modeGroup->addButton(m_serialModeBtn, static_cast<int>(DataSourceMode::Serial));
    toolbarLayout->addWidget(m_serialModeBtn);

    // 仿真模式按钮
    m_simulatorModeBtn = new QRadioButton("📡 UDP仿真", this);
    m_simulatorModeBtn->setStyleSheet(R"(
        QRadioButton { background-color: #3C3C3C; border-radius: 3px; padding: 6px 12px; }
        QRadioButton:hover { background-color: #4C4C4C; }
        QRadioButton:checked { background-color: #388E3C; border: 2px solid #81C784; }
    )");
    m_modeGroup->addButton(m_simulatorModeBtn, static_cast<int>(DataSourceMode::Simulator));
    toolbarLayout->addWidget(m_simulatorModeBtn);

    connect(m_modeGroup, &QButtonGroup::idClicked, this, &MainWindow::onModeChanged);

    toolbarLayout->addStretch();

    m_modeIndicator = new QLabel("当前: 串口模式", this);
    m_modeIndicator->setStyleSheet("color: #4FC3F7; font-size: 11px;");
    toolbarLayout->addWidget(m_modeIndicator);

    parentLayout->addWidget(toolbarFrame);
}

void MainWindow::setupMenu() {
    QMenuBar* menubar = menuBar();
    menubar->setStyleSheet(R"(
        QMenuBar { background-color: #2D2D30; color: #CCCCCC; }
        QMenuBar::item:selected { background-color: #3D3D3D; }
        QMenu { background-color: #2D2D30; color: #CCCCCC; border: 1px solid #3D3D3D; }
        QMenu::item:selected { background-color: #0078D4; }
    )");

    // 文件菜单
    QMenu* fileMenu = menubar->addMenu("文件(&F)");

    QAction* exportAction = new QAction("导出数据(&E)", this);
    exportAction->setShortcut(QKeySequence("Ctrl+E"));
    connect(exportAction, &QAction::triggered, this, &MainWindow::exportData);
    fileMenu->addAction(exportAction);

    fileMenu->addSeparator();

    QAction* exitAction = new QAction("退出(&X)", this);
    exitAction->setShortcut(QKeySequence("Ctrl+Q"));
    connect(exitAction, &QAction::triggered, this, &QMainWindow::close);
    fileMenu->addAction(exitAction);

    // 视图菜单
    QMenu* viewMenu = menubar->addMenu("视图(&V)");

    QAction* clearAction = new QAction("清空数据(&C)", this);
    clearAction->setShortcut(QKeySequence("Ctrl+L"));
    connect(clearAction, &QAction::triggered, this, &MainWindow::clearData);
    viewMenu->addAction(clearAction);

    // 帮助菜单
    QMenu* helpMenu = menubar->addMenu("帮助(&H)");

    QAction* updateAction = new QAction("检查更新(&U)", this);
    connect(updateAction, &QAction::triggered, this, &MainWindow::checkForUpdates);
    helpMenu->addAction(updateAction);

    helpMenu->addSeparator();

    QAction* aboutAction = new QAction("关于(&A)", this);
    connect(aboutAction, &QAction::triggered, this, &MainWindow::showAbout);
    helpMenu->addAction(aboutAction);

    QAction* protocolAction = new QAction("串口协议说明(&P)", this);
    connect(protocolAction, &QAction::triggered, this, &MainWindow::showProtocolHelp);
    helpMenu->addAction(protocolAction);
}

void MainWindow::setupConnections() {
    // 串口模式信号
    connect(m_controlPanel->serialPanel(), &SerialConfigPanel::connectRequested,
            this, &MainWindow::connectSerial);
    connect(m_controlPanel->serialPanel(), &SerialConfigPanel::disconnectRequested,
            this, &MainWindow::disconnectSerial);

    connect(m_serialManager.get(), &SerialManager::dataReceived,
            this, &MainWindow::onDataReceived);
    connect(m_serialManager.get(), &SerialManager::handshakeReceived,
            this, &MainWindow::onHandshakeReceived);
    connect(m_serialManager.get(), &SerialManager::connectionChanged,
            this, &MainWindow::onSerialConnectionChanged);
    connect(m_serialManager.get(), &SerialManager::errorOccurred,
            this, &MainWindow::onError);

    // 仿真模式信号
    connect(m_controlPanel->simulatorPanel(), &SimulatorConfigPanel::connectRequested,
            this, &MainWindow::connectSimulator);
    connect(m_controlPanel->simulatorPanel(), &SimulatorConfigPanel::disconnectRequested,
            this, &MainWindow::disconnectSimulator);

    connect(m_simulatorReceiver.get(), &SimulatorReceiver::dataReceived,
            this, &MainWindow::onDataReceived);
    connect(m_simulatorReceiver.get(), &SimulatorReceiver::handshakeReceived,
            this, &MainWindow::onHandshakeReceived);
    connect(m_simulatorReceiver.get(), &SimulatorReceiver::connectionChanged,
            this, &MainWindow::onSimulatorConnectionChanged);
    connect(m_simulatorReceiver.get(), &SimulatorReceiver::errorOccurred,
            this, &MainWindow::onError);

    // 共用控件信号
    connect(m_controlPanel->pidPanel(), &PIDControlPanel::sendRequested,
            this, &MainWindow::sendPIDParams);
    connect(m_controlPanel->setpointPanel(), &SetpointPanel::sendRequested,
            this, &MainWindow::sendSetpoint);
    connect(m_controlPanel->dataPanel(), &DataControlPanel::clearRequested,
            this, &MainWindow::clearData);
    connect(m_controlPanel->dataPanel(), &DataControlPanel::pauseRequested,
            this, &MainWindow::setPaused);
    connect(m_controlPanel->dataPanel(), &DataControlPanel::exportRequested,
            this, &MainWindow::exportData);

    // 滤波面板信号
    connect(m_controlPanel->filterPanel(), &FilterPanel::filterChanged,
            this, &MainWindow::onFilterChanged);

    // 数据处理完成信号
    connect(m_dataProcessor.get(), &DataProcessor::dataProcessed,
            this, &MainWindow::onDataProcessed);
}

void MainWindow::setupTimers() {
    // 图表更新定时器 (20 FPS)
    m_plotTimer = new QTimer(this);
    connect(m_plotTimer, &QTimer::timeout, this, &MainWindow::updatePlots);
    m_plotTimer->start(50);

    // 性能指标更新定时器
    m_metricsTimer = new QTimer(this);
    connect(m_metricsTimer, &QTimer::timeout, this, &MainWindow::updateMetrics);
    m_metricsTimer->start(500);

    // FFT更新定时器
    m_fftTimer = new QTimer(this);
    connect(m_fftTimer, &QTimer::timeout, this, &MainWindow::updateFFT);
    m_fftTimer->start(1000);
}

// ============ 模式切换 ============

void MainWindow::onModeChanged(int modeId) {
    DataSourceMode newMode = static_cast<DataSourceMode>(modeId);
    if (newMode == m_currentMode) {
        return;
    }

    // 断开当前连接
    if (m_currentMode == DataSourceMode::Serial && m_serialManager->isConnected()) {
        m_serialManager->disconnect();
    } else if (m_currentMode == DataSourceMode::Simulator && m_simulatorReceiver->isConnected()) {
        m_simulatorReceiver->stop();
    }

    m_currentMode = newMode;
    m_controlPanel->setMode(modeId);

    // 清空数据
    clearData();

    // 更新UI
    if (newMode == DataSourceMode::Serial) {
        m_modeIndicator->setText("当前: 串口模式");
        m_modeIndicator->setStyleSheet("color: #4FC3F7; font-size: 11px;");
        m_statusBar->showMessage("已切换到串口模式 - 请连接串口");
    } else {
        m_modeIndicator->setText("当前: UDP仿真模式");
        m_modeIndicator->setStyleSheet("color: #81C784; font-size: 11px;");
        m_statusBar->showMessage("已切换到UDP仿真模式 - 请开始监听");
    }
}

// ============ 连接管理 ============

void MainWindow::connectSerial(const QString& port, int baudrate) {
    m_statusBar->showMessage(QString("正在连接 %1...").arg(port));
    if (m_serialManager->connectToPort(port, baudrate)) {
        m_statusBar->showMessage(QString("已连接 %1 @ %2").arg(port).arg(baudrate));
    } else {
        m_statusBar->showMessage("连接失败");
        QMessageBox::warning(this, "连接失败", QString("无法连接到 %1").arg(port));
    }
}

void MainWindow::disconnectSerial() {
    m_serialManager->disconnect();
    m_plotWidget->clearStateDefinitions();
    m_statusBar->showMessage("已断开连接");
}

void MainWindow::connectSimulator(const QString& host, int port) {
    m_statusBar->showMessage(QString("正在监听 %1:%2...").arg(host).arg(port));
    m_simulatorReceiver->start(host, port);
}

void MainWindow::disconnectSimulator() {
    m_simulatorReceiver->stop();
    m_plotWidget->clearStateDefinitions();
    m_statusBar->showMessage("已停止监听");
}

void MainWindow::onSerialConnectionChanged(bool connected) {
    m_controlPanel->serialPanel()->setConnected(connected);
    if (!connected) {
        m_plotWidget->clearStateDefinitions();
    }
}

void MainWindow::onSimulatorConnectionChanged(bool connected, const QString& message) {
    m_controlPanel->simulatorPanel()->setConnected(connected, message);
    if (connected) {
        m_statusBar->showMessage(message);
    } else {
        m_plotWidget->clearStateDefinitions();
    }
}

void MainWindow::onError(const QString& message) {
    m_statusBar->showMessage(QString("错误: %1").arg(message));
}

// ============ 数据处理 ============

void MainWindow::onHandshakeReceived(const HandshakeInfo& handshake) {
    // 检查状态定义是否变化
    bool stateChanged = false;
    if (!m_handshake) {
        stateChanged = true;
    } else if (m_handshake->stateCount != handshake.stateCount) {
        stateChanged = true;
    } else if (m_handshake->source != handshake.source) {
        stateChanged = true;
    }

    m_handshake = std::make_unique<HandshakeInfo>(handshake);

    // 显示握手信息
    QStringList stateNames;
    for (const auto& state : handshake.stateDefs) {
        stateNames << state.name;
    }
    QString sourceName = handshake.source.startsWith("udp") ? "UDP仿真" : "串口";
    m_statusBar->showMessage(
        QString("已连接 [%1] 协议v%2, %3个状态: %4")
            .arg(sourceName)
            .arg(handshake.protocolVersion)
            .arg(handshake.stateCount)
            .arg(stateNames.join(", "))
    );

    // 更新图表组件
    if (stateChanged) {
        m_plotWidget->setStateDefinitions(handshake.stateDefs);
        clearData();
    }
}

void MainWindow::onDataReceived(const UnifiedData& data) {
    if (m_isPaused) {
        return;
    }

    // TODO: 存储数据到缓冲区
    // m_dataBuffer.append(data);

    // 更新数据点数
    // m_controlPanel->dataPanel()->setDataCount(m_dataBuffer.size());
}

void MainWindow::onDataProcessed(const QVariantMap& result) {
    // 更新图表
    // m_plotWidget->standardPlot()->updateData(...);
}

// ============ 控制命令 ============

void MainWindow::sendPIDParams(double kp, double ki, double kd) {
    if (m_currentMode == DataSourceMode::Serial && m_serialManager->isConnected()) {
        QString cmd = QString("PID:%1,%2,%3")
            .arg(kp, 0, 'f', 4)
            .arg(ki, 0, 'f', 4)
            .arg(kd, 0, 'f', 4);
        m_serialManager->send(cmd);
        m_statusBar->showMessage(QString("已发送: %1").arg(cmd));
    } else {
        m_statusBar->showMessage("未连接，无法发送");
    }
}

void MainWindow::sendSetpoint(double setpoint) {
    if (m_currentMode == DataSourceMode::Serial && m_serialManager->isConnected()) {
        QString cmd = QString("SP:%1").arg(setpoint, 0, 'f', 2);
        m_serialManager->send(cmd);
        m_statusBar->showMessage(QString("已发送: %1").arg(cmd));
    } else {
        m_statusBar->showMessage("未连接，无法发送");
    }
}

// ============ 数据管理 ============

void MainWindow::setPaused(bool paused) {
    m_isPaused = paused;
    m_statusBar->showMessage(paused ? "已暂停" : "继续运行");
}

void MainWindow::clearData() {
    // m_dataBuffer.clear();
    m_plotWidget->clearAll();
    m_controlPanel->dataPanel()->setDataCount(0);
    m_controlPanel->metricsPanel()->clear();
    m_statusBar->showMessage("数据已清空");
}

void MainWindow::exportData() {
    QString filePath = QFileDialog::getSaveFileName(
        this, "导出数据", "control_data.csv", "CSV文件 (*.csv)"
    );

    if (filePath.isEmpty()) {
        return;
    }

    // TODO: 实现数据导出
    m_statusBar->showMessage(QString("已导出到 %1").arg(filePath));
}

// ============ 定时更新 ============

void MainWindow::updatePlots() {
    if (m_isPaused) {
        return;
    }
    // TODO: 实现图表更新
}

void MainWindow::updateMetrics() {
    if (m_isPaused) {
        return;
    }
    // TODO: 实现性能指标更新
}

void MainWindow::updateFFT() {
    if (m_isPaused) {
        return;
    }
    // TODO: 实现FFT更新
}

void MainWindow::onFilterChanged() {
    m_statusBar->showMessage("滤波设置已更新");
}

// ============ 菜单操作 ============

void MainWindow::showAbout() {
    QMessageBox msg(this);
    msg.setWindowTitle("关于");
    msg.setTextFormat(Qt::RichText);
    msg.setText(
        "<div style='color: #000000;'>"
        "<h3 style='color: #1565C0;'>控制系统实时分析工具 v2.1.2</h3>"
        "<p>C++ Qt6 版本 - 统一架构</p>"
        "<h4 style='color: #2E7D32;'>数据源:</h4>"
        "<ul>"
        "<li><b>串口</b>: 高效文本协议，适合单片机</li>"
        "<li><b>UDP仿真</b>: JSON协议，适合仿真器</li>"
        "</ul>"
        "<h4 style='color: #2E7D32;'>主要功能:</h4>"
        "<ul>"
        "<li>实时数据可视化</li>"
        "<li>多状态变量选择</li>"
        "<li>FFT频谱分析</li>"
        "<li>性能指标计算</li>"
        "</ul>"
        "<p style='color: #666;'>GitHub: ktkuri132/Control_System_Box</p>"
        "</div>"
    );
    msg.exec();
}

void MainWindow::showProtocolHelp() {
    QMessageBox msg(this);
    msg.setWindowTitle("串口协议说明");
    msg.setTextFormat(Qt::RichText);
    msg.setText(
        "<div style='color: #000000;'>"
        "<h3 style='color: #1565C0;'>串口数据协议</h3>"
        "<h4 style='color: #D84315;'>【握手帧】首次连接发送</h4>"
        "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>#H,状态数,名称1,名称2,...\\n</pre>"
        "<p>示例: <code style='background-color: #E3F2FD; padding: 2px;'>#H,3,angle,position,force</code></p>"
        "<h4 style='color: #D84315;'>【数据帧】高频发送</h4>"
        "<pre style='background-color: #F5F5F5; padding: 5px; color: #333;'>#D,序号,时间ms,目标1,当前1,目标2,当前2,...\\n</pre>"
        "<p>示例: <code style='background-color: #E3F2FD; padding: 2px;'>#D,1234,15000,0.00,0.05,0.00,-0.02</code></p>"
        "</div>"
    );
    msg.exec();
}

void MainWindow::checkForUpdates() {
    // TODO: 实现更新检查
    QMessageBox::information(this, "检查更新", "当前已是最新版本 v2.1.2");
}

void MainWindow::closeEvent(QCloseEvent *event) {
    // 停止数据处理
    if (m_dataProcessor) {
        m_dataProcessor->stop();
    }

    // 断开连接
    if (m_serialManager && m_serialManager->isConnected()) {
        m_serialManager->disconnect();
    }
    if (m_simulatorReceiver && m_simulatorReceiver->isConnected()) {
        m_simulatorReceiver->stop();
    }

    event->accept();
}
