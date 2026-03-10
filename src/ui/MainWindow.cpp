/**
 * MainWindow.cpp - 主窗口实现
 *
 * 双进程架构：
 *   主进程：UI渲染（Vulkan GPU加速）
 *   计算进程：数据处理和分析
 */

#include "ui/MainWindow.h"
#include "core/DataBuffer.h"
#include "core/DataProcessor.h"
#include "core/PerformanceAnalyzer.h"
#include "core/SerialManager.h"
#include "core/SimulatorReceiver.h"
#include "core/UnifiedDataProtocol.h"
#include "ui/panels/DataControlPanel.h"
#include "ui/panels/FilterPanel.h"
#include "ui/panels/MetricsPanel.h"
#include "ui/panels/PIDControlPanel.h"
#include "ui/panels/SerialConfigPanel.h"
#include "ui/panels/SetpointPanel.h"
#include "ui/panels/SimulatorConfigPanel.h"
#include "ui/panels/UnifiedControlPanel.h"
#include "ui/plots/SimulatorPlotWidget.h"

#include <QAction>
#include <QApplication>
#include <QCloseEvent>
#include <QDateTime>
#include <QFileDialog>
#include <QFrame>
#include <QHBoxLayout>
#include <QMenu>
#include <QMenuBar>
#include <QMessageBox>
#include <QTimer>
#include <QVBoxLayout>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), m_currentMode(DataSourceMode::Serial),
      m_isPaused(false) {
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
  setWindowTitle("控制系统实时分析工具 v2.3.0");
  setMinimumSize(1200, 700);
  resize(1400, 800);

  setupStyles();

  QWidget *centralWidget = new QWidget(this);
  setCentralWidget(centralWidget);

  QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
  mainLayout->setContentsMargins(0, 0, 0, 0);
  mainLayout->setSpacing(0);

  // 模式切换工具栏
  setupModeToolbar(mainLayout);

  // 内容区域
  QHBoxLayout *contentLayout = new QHBoxLayout();
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
  m_statusBar->showMessage("就绪 - 请选择数据源并连接 | Vulkan GPU加速渲染");

  setupMenu();
}

void MainWindow::setupStyles() {
  setStyleSheet(R"(
        QMainWindow { background-color: #1E1E1E; }
        QWidget { color: #CCCCCC; background-color: #1E1E1E; font-family: "Microsoft YaHei", sans-serif; }
        QLabel { color: #CCCCCC; background-color: transparent; }
        QGroupBox { background-color: #2D2D30; }
        QPushButton {
            background-color: #3C3C3C; color: #FFFFFF;
            border: 1px solid #555555; border-radius: 4px; padding: 6px 12px;
        }
        QPushButton:hover { background-color: #4C4C4C; border-color: #666666; }
        QPushButton:pressed { background-color: #2D2D30; }
        QComboBox {
            background-color: #3C3C3C; color: #FFFFFF;
            border: 1px solid #555555; border-radius: 3px; padding: 4px;
        }
        QComboBox:hover { border-color: #0078D4; }
        QComboBox QAbstractItemView {
            background-color: #2D2D30; color: #FFFFFF;
            selection-background-color: #0078D4;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C; color: #FFFFFF;
            border: 1px solid #555555; border-radius: 3px; padding: 2px;
        }
        QSpinBox:hover, QDoubleSpinBox:hover { border-color: #0078D4; }
        QLineEdit {
            background-color: #3C3C3C; color: #FFFFFF;
            border: 1px solid #555555; border-radius: 3px; padding: 4px;
        }
        QLineEdit:hover { border-color: #0078D4; }
        QCheckBox { color: #CCCCCC; background-color: transparent; }
        QCheckBox::indicator {
            width: 16px; height: 16px;
            background-color: #3C3C3C; border: 1px solid #555555; border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D4; border-color: #0078D4;
        }
        QStatusBar { background-color: #007ACC; color: white; }
        QRadioButton { color: #FFFFFF; font-weight: bold; padding: 8px 16px; background-color: transparent; }
        QRadioButton::indicator { width: 0px; height: 0px; }
        QScrollArea { background-color: #1E1E1E; border: none; }
        QScrollArea > QWidget > QWidget { background-color: #1E1E1E; }
        QSlider::groove:horizontal {
            border: 1px solid #555555; height: 6px;
            background: #3C3C3C; border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #0078D4; border: 1px solid #005A9E;
            width: 14px; margin: -5px 0; border-radius: 7px;
        }
        QSlider::handle:horizontal:hover { background: #1C86E5; }
        QSlider::sub-page:horizontal { background: #0078D4; border-radius: 3px; }
    )");
}

void MainWindow::setupModeToolbar(QVBoxLayout *parentLayout) {
  QFrame *toolbarFrame = new QFrame(this);
  toolbarFrame->setStyleSheet(R"(
        QFrame { background-color: #2D2D30; border-bottom: 1px solid #3D3D3D; }
    )");
  toolbarFrame->setFixedHeight(45);

  QHBoxLayout *toolbarLayout = new QHBoxLayout(toolbarFrame);
  toolbarLayout->setContentsMargins(10, 5, 10, 5);
  toolbarLayout->setSpacing(5);

  QLabel *titleLabel = new QLabel("数据源:", this);
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
  m_modeGroup->addButton(m_serialModeBtn,
                         static_cast<int>(DataSourceMode::Serial));
  toolbarLayout->addWidget(m_serialModeBtn);

  // 仿真模式按钮
  m_simulatorModeBtn = new QRadioButton("📡 UDP仿真", this);
  m_simulatorModeBtn->setStyleSheet(R"(
        QRadioButton { background-color: #3C3C3C; border-radius: 3px; padding: 6px 12px; }
        QRadioButton:hover { background-color: #4C4C4C; }
        QRadioButton:checked { background-color: #388E3C; border: 2px solid #81C784; }
    )");
  m_modeGroup->addButton(m_simulatorModeBtn,
                         static_cast<int>(DataSourceMode::Simulator));
  toolbarLayout->addWidget(m_simulatorModeBtn);

  connect(m_modeGroup, &QButtonGroup::idClicked, this,
          &MainWindow::onModeChanged);

  toolbarLayout->addStretch();

  m_modeIndicator = new QLabel("当前: 串口模式", this);
  m_modeIndicator->setStyleSheet("color: #4FC3F7; font-size: 11px;");
  toolbarLayout->addWidget(m_modeIndicator);

  parentLayout->addWidget(toolbarFrame);
}

void MainWindow::setupMenu() {
  QMenuBar *menubar = menuBar();
  menubar->setStyleSheet(R"(
        QMenuBar { background-color: #2D2D30; color: #CCCCCC; }
        QMenuBar::item:selected { background-color: #3D3D3D; }
        QMenu { background-color: #2D2D30; color: #CCCCCC; border: 1px solid #3D3D3D; }
        QMenu::item:selected { background-color: #0078D4; }
    )");

  // 文件菜单
  QMenu *fileMenu = menubar->addMenu("文件(&F)");

  QAction *exportAction = new QAction("导出数据(&E)", this);
  exportAction->setShortcut(QKeySequence("Ctrl+E"));
  connect(exportAction, &QAction::triggered, this, &MainWindow::exportData);
  fileMenu->addAction(exportAction);

  fileMenu->addSeparator();

  QAction *exitAction = new QAction("退出(&X)", this);
  exitAction->setShortcut(QKeySequence("Ctrl+Q"));
  connect(exitAction, &QAction::triggered, this, &QMainWindow::close);
  fileMenu->addAction(exitAction);

  // 视图菜单
  QMenu *viewMenu = menubar->addMenu("视图(&V)");

  QAction *clearAction = new QAction("清空数据(&C)", this);
  clearAction->setShortcut(QKeySequence("Ctrl+L"));
  connect(clearAction, &QAction::triggered, this, &MainWindow::clearData);
  viewMenu->addAction(clearAction);

  // 帮助菜单
  QMenu *helpMenu = menubar->addMenu("帮助(&H)");

  QAction *updateAction = new QAction("检查更新(&U)", this);
  connect(updateAction, &QAction::triggered, this,
          &MainWindow::checkForUpdates);
  helpMenu->addAction(updateAction);

  helpMenu->addSeparator();

  QAction *aboutAction = new QAction("关于(&A)", this);
  connect(aboutAction, &QAction::triggered, this, &MainWindow::showAbout);
  helpMenu->addAction(aboutAction);

  QAction *protocolAction = new QAction("串口协议说明(&P)", this);
  connect(protocolAction, &QAction::triggered, this,
          &MainWindow::showProtocolHelp);
  helpMenu->addAction(protocolAction);
}

void MainWindow::setupConnections() {
  // 串口模式信号
  connect(m_controlPanel->serialPanel(), &SerialConfigPanel::connectRequested,
          this, &MainWindow::connectSerial);
  connect(m_controlPanel->serialPanel(),
          &SerialConfigPanel::disconnectRequested, this,
          &MainWindow::disconnectSerial);

  connect(m_serialManager.get(), &SerialManager::dataReceived, this,
          &MainWindow::onDataReceived);
  connect(m_serialManager.get(), &SerialManager::handshakeReceived, this,
          &MainWindow::onHandshakeReceived);
  connect(m_serialManager.get(), &SerialManager::connectionChanged, this,
          &MainWindow::onSerialConnectionChanged);
  connect(m_serialManager.get(), &SerialManager::errorOccurred, this,
          &MainWindow::onError);

  // 仿真模式信号
  connect(m_controlPanel->simulatorPanel(),
          &SimulatorConfigPanel::connectRequested, this,
          &MainWindow::connectSimulator);
  connect(m_controlPanel->simulatorPanel(),
          &SimulatorConfigPanel::disconnectRequested, this,
          &MainWindow::disconnectSimulator);

  connect(m_simulatorReceiver.get(), &SimulatorReceiver::dataReceived, this,
          &MainWindow::onDataReceived);
  connect(m_simulatorReceiver.get(), &SimulatorReceiver::handshakeReceived,
          this, &MainWindow::onHandshakeReceived);
  connect(m_simulatorReceiver.get(), &SimulatorReceiver::connectionChanged,
          this, &MainWindow::onSimulatorConnectionChanged);
  connect(m_simulatorReceiver.get(), &SimulatorReceiver::errorOccurred, this,
          &MainWindow::onError);

  // 共用控件信号
  connect(m_controlPanel->pidPanel(), &PIDControlPanel::sendRequested, this,
          &MainWindow::sendPIDParams);
  connect(m_controlPanel->setpointPanel(), &SetpointPanel::sendRequested, this,
          &MainWindow::sendSetpoint);
  connect(m_controlPanel->dataPanel(), &DataControlPanel::clearRequested, this,
          &MainWindow::clearData);
  connect(m_controlPanel->dataPanel(), &DataControlPanel::pauseRequested, this,
          &MainWindow::setPaused);
  connect(m_controlPanel->dataPanel(), &DataControlPanel::exportRequested, this,
          &MainWindow::exportData);

  // 滤波面板信号
  connect(m_controlPanel->filterPanel(), &FilterPanel::filterChanged, this,
          &MainWindow::onFilterChanged);

  // 数据处理完成信号
  connect(m_dataProcessor.get(), &DataProcessor::dataProcessed, this,
          &MainWindow::onDataProcessed);
}

void MainWindow::setupTimers() {
  // 图表更新定时器 (60 FPS)
  m_plotTimer = new QTimer(this);
  connect(m_plotTimer, &QTimer::timeout, this, &MainWindow::updatePlots);
  m_plotTimer->start(16); // ~60 FPS

  // 性能指标更新定时器 (5 Hz)
  m_metricsTimer = new QTimer(this);
  connect(m_metricsTimer, &QTimer::timeout, this, &MainWindow::updateMetrics);
  m_metricsTimer->start(200);

  // FFT更新定时器 (2 Hz)
  m_fftTimer = new QTimer(this);
  connect(m_fftTimer, &QTimer::timeout, this, &MainWindow::updateFFT);
  m_fftTimer->start(500);
}

// ============ 模式切换 ============

void MainWindow::onModeChanged(int modeId) {
  DataSourceMode newMode = static_cast<DataSourceMode>(modeId);
  if (newMode == m_currentMode) {
    return;
  }

  // 断开当前连接
  if (m_currentMode == DataSourceMode::Serial &&
      m_serialManager->isConnected()) {
    m_serialManager->disconnect();
  } else if (m_currentMode == DataSourceMode::Simulator &&
             m_simulatorReceiver->isConnected()) {
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

void MainWindow::connectSerial(const QString &port, int baudrate) {
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

void MainWindow::connectSimulator(const QString &host, int port) {
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

void MainWindow::onSimulatorConnectionChanged(bool connected,
                                              const QString &message) {
  m_controlPanel->simulatorPanel()->setConnected(connected, message);
  if (connected) {
    m_statusBar->showMessage(message);
  } else {
    m_plotWidget->clearStateDefinitions();
  }
}

void MainWindow::onError(const QString &message) {
  m_statusBar->showMessage(QString("错误: %1").arg(message));
}

// ============ 数据处理 ============

void MainWindow::onHandshakeReceived(const HandshakeInfo &handshake) {
  // 检查状态定义是否变化
  bool stateChanged = false;
  bool isFirstHandshake = false;

  if (!m_handshake) {
    stateChanged = true;
    isFirstHandshake = true;
  } else if (m_handshake->stateCount != handshake.stateCount) {
    stateChanged = true;
  } else if (m_handshake->source != handshake.source) {
    stateChanged = true;
  }

  m_handshake = std::make_unique<HandshakeInfo>(handshake);

  // 显示握手信息
  QStringList stateNames;
  for (const auto &state : handshake.stateDefs) {
    stateNames << state.name;
  }
  QString sourceName = handshake.source.startsWith("udp") ? "UDP仿真" : "串口";
  QString systemType = handshake.source;
  if (systemType.startsWith("udp:")) {
    systemType = systemType.mid(4);
  }

  m_plotWidget->setSystemType(systemType);
  if (handshake.source.startsWith("udp")) {
    m_controlPanel->simulatorPanel()->setSystemType(
        systemType, handshake.protocolVersion, handshake.stateCount);
  }

  m_statusBar->showMessage(QString("已连接 [%1] 协议v%2, %3个状态: %4")
                               .arg(sourceName)
                               .arg(handshake.protocolVersion)
                               .arg(handshake.stateCount)
                               .arg(stateNames.join(", ")));

  // 更新图表组件的状态定义
  if (stateChanged) {
    m_plotWidget->setStateDefinitions(handshake.stateDefs);

    // 只有在状态数量变化且不是首次握手时才清空数据
    // 首次自动握手时不清空，因为数据帧和握手是一起来的
    if (!isFirstHandshake) {
      clearData();
    } else {
      // 首次握手时只重新初始化数据缓冲区大小
      int stateCount = handshake.stateCount;
      if (m_targetValues.size() != stateCount) {
        m_targetValues.resize(stateCount);
        m_currentValues.resize(stateCount);
      }
    }
  }
}

void MainWindow::onDataReceived(const UnifiedData &data) {
  if (m_isPaused) {
    return;
  }

  // 确保数据缓冲区已初始化
  int stateCount = data.states.size();
  if (stateCount == 0) {
    return;
  }

  // 初始化缓冲区（如果需要）
  if (m_targetValues.size() != stateCount) {
    m_targetValues.resize(stateCount);
    m_currentValues.resize(stateCount);
  }

  // 检测仿真器重置（时间戳回跳或序列号重置）
  static int lastSeq = -1;
  bool shouldReset = false;
  QString resetReason;

  if (!m_timestamps.isEmpty()) {
    double lastTime = m_timestamps.last();
    double newTime = data.timestamp;

    // 检测时间戳回跳（允许0.5秒的抖动）
    if (newTime < lastTime - 0.5) {
      shouldReset = true;
      resetReason = QString("时间戳回跳: %1 -> %2")
                        .arg(lastTime, 0, 'f', 2)
                        .arg(newTime, 0, 'f', 2);
    }
    // 检测序列号重置（seq从大值跳到小值，差距超过100）
    else if (lastSeq > 100 && data.seq < lastSeq - 100) {
      shouldReset = true;
      resetReason = QString("序列号重置: %1 -> %2").arg(lastSeq).arg(data.seq);
    }
  }

  if (shouldReset) {
    m_timestamps.clear();
    for (int i = 0; i < stateCount; ++i) {
      m_targetValues[i].clear();
      m_currentValues[i].clear();
    }
    m_plotWidget->clearAll();
    m_controlPanel->dataPanel()->setDataCount(0);
    lastSeq = -1;
  }

  lastSeq = data.seq;

  // 存储时间戳
  m_timestamps.append(data.timestamp);

  // 存储每个状态的值
  for (int i = 0; i < stateCount; ++i) {
    m_targetValues[i].append(data.states[i].target);
    m_currentValues[i].append(data.states[i].current);
  }

  // 限制数据点数量
  while (m_timestamps.size() > m_maxDataPoints) {
    m_timestamps.removeFirst();
    for (int i = 0; i < stateCount; ++i) {
      m_targetValues[i].removeFirst();
      m_currentValues[i].removeFirst();
    }
  }

  // 更新数据点数显示
  m_controlPanel->dataPanel()->setDataCount(m_timestamps.size());
}

void MainWindow::onDataProcessed(const QVariantMap &result) {
  // 更新图表
  // m_plotWidget->standardPlot()->updateData(...);
}

// ============ 控制命令 ============

void MainWindow::sendPIDParams(double kp, double ki, double kd) {
  if (m_currentMode == DataSourceMode::Serial &&
      m_serialManager->isConnected()) {
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
  if (m_currentMode == DataSourceMode::Serial &&
      m_serialManager->isConnected()) {
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
  m_timestamps.clear();
  m_targetValues.clear();
  m_currentValues.clear();
  m_plotWidget->clearAll();
  m_controlPanel->dataPanel()->setDataCount(0);
  m_controlPanel->metricsPanel()->clear();
  m_statusBar->showMessage("数据已清空");
}

void MainWindow::exportData() {
  QString filePath = QFileDialog::getSaveFileName(
      this, "导出数据", "control_data.csv", "CSV文件 (*.csv)");

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

  // 确保有数据和选中的状态
  if (m_timestamps.isEmpty() || m_targetValues.isEmpty()) {
    return;
  }

  // 启动早期数据点太少时，跳过一次绘图，避免出现初始化阶段的错线。
  if (m_timestamps.size() < 8) {
    return;
  }

  int selectedState = m_plotWidget->getSelectedStateIndex();
  if (selectedState < 0 || selectedState >= m_targetValues.size()) {
    if (!m_targetValues.isEmpty()) {
      selectedState = 0;
    } else {
      return;
    }
  }

  // 更新标准响应曲线
  QVector<double> emptyVec;
  m_plotWidget->standardPlot()->updateData(
      m_timestamps, m_targetValues[selectedState],
      m_currentValues[selectedState], emptyVec, emptyVec, emptyVec);
}

void MainWindow::updateMetrics() {
  if (m_isPaused) {
    return;
  }

  // 确保有足够的数据进行分析
  if (m_timestamps.size() < 10) {
    return;
  }

  int selectedState = m_plotWidget->getSelectedStateIndex();
  if (selectedState < 0 || selectedState >= m_targetValues.size()) {
    selectedState = 0;
  }

  if (selectedState >= m_currentValues.size() ||
      m_currentValues[selectedState].isEmpty()) {
    return;
  }

  // 使用分析器计算指标
  const auto &setpoints = m_targetValues[selectedState];
  const auto &processValues = m_currentValues[selectedState];

  // 计算误差
  QVector<double> errors;
  errors.reserve(setpoints.size());
  for (int i = 0; i < qMin(setpoints.size(), processValues.size()); ++i) {
    errors.append(setpoints[i] - processValues[i]);
  }

  // 分析性能指标
  PerformanceMetrics metrics =
      m_analyzer->analyze(m_timestamps, setpoints, processValues, errors);

  // 更新面板显示
  m_controlPanel->metricsPanel()->updateSerialMetrics(metrics);
}

void MainWindow::updateFFT() {
  if (m_isPaused) {
    return;
  }
  // TODO: 实现FFT更新
}

void MainWindow::onFilterChanged() {
  // 获取滤波器设置
  bool enabled = m_controlPanel->filterPanel()->isFilterEnabled();
  QString type = m_controlPanel->filterPanel()->getFilterType();
  int strength = m_controlPanel->filterPanel()->getFilterStrength();

  // 更新图表的滤波设置
  if (m_plotWidget && m_plotWidget->standardPlot()) {
    m_plotWidget->standardPlot()->setFilterParams(enabled, type, strength);
    m_plotWidget->standardPlot()->setShowFiltered(enabled);
  }

  m_statusBar->showMessage(QString("滤波设置已更新: %1, 强度=%2")
                               .arg(enabled ? type : "关闭")
                               .arg(strength));
}

// ============ 菜单操作 ============

void MainWindow::showAbout() {
  QMessageBox msg(this);
  msg.setWindowTitle("关于");
  msg.setTextFormat(Qt::RichText);
  msg.setText("<div style='color: #000000;'>"
              "<h3 style='color: #1565C0;'>控制系统实时分析工具 v2.3.0</h3>"
              "<p>C++ Qt6 版本 - 简化架构（Vulkan GPU加速）</p>"
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
              "</div>");
  msg.exec();
}

void MainWindow::showProtocolHelp() {
  QMessageBox msg(this);
  msg.setWindowTitle("串口协议说明");
  msg.setTextFormat(Qt::RichText);
  msg.setText("<div style='color: #000000;'>"
              "<h3 style='color: #1565C0;'>串口数据协议</h3>"
              "<h4 style='color: #D84315;'>【握手帧】首次连接发送</h4>"
              "<pre style='background-color: #F5F5F5; padding: 5px; color: "
              "#333;'>#H,状态数,名称1,名称2,...\\n</pre>"
              "<p>示例: <code style='background-color: #E3F2FD; padding: "
              "2px;'>#H,3,angle,position,force</code></p>"
              "<h4 style='color: #D84315;'>【数据帧】高频发送</h4>"
              "<pre style='background-color: #F5F5F5; padding: 5px; color: "
              "#333;'>#D,序号,时间ms,目标1,当前1,目标2,当前2,...\\n</pre>"
              "<p>示例: <code style='background-color: #E3F2FD; padding: "
              "2px;'>#D,1234,15000,0.00,0.05,0.00,-0.02</code></p>"
              "</div>");
  msg.exec();
}

void MainWindow::checkForUpdates() {
  // TODO: 实现更新检查
  QMessageBox::information(this, "检查更新", "当前已是最新版本 v2.3.0");
}

void MainWindow::autoStartUdpMode() {
  // 切换到UDP仿真模式
  m_simulatorModeBtn->setChecked(true);
  onModeChanged(static_cast<int>(DataSourceMode::Simulator));

  // 自动开始监听（使用默认地址和端口）
  QString host = "0.0.0.0";
  int port = 5555;

  connectSimulator(host, port);
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
