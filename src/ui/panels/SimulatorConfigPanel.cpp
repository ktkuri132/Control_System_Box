/**
 * SimulatorConfigPanel.cpp - 仿真配置面板实现
 */

#include "ui/panels/SimulatorConfigPanel.h"

#include <QGridLayout>
#include <QLabel>

SimulatorConfigPanel::SimulatorConfigPanel(QWidget* parent)
    : QGroupBox("仿真数据接收 (UDP)", parent)
{
    setupUi();
    applyStyles();
}

void SimulatorConfigPanel::setupUi() {
    QGridLayout* layout = new QGridLayout(this);
    layout->setSpacing(8);

    // IP地址
    layout->addWidget(new QLabel("IP地址:"), 0, 0);
    m_hostEdit = new QLineEdit("127.0.0.1");
    m_hostEdit->setPlaceholderText("127.0.0.1");
    layout->addWidget(m_hostEdit, 0, 1, 1, 2);

    // 端口
    layout->addWidget(new QLabel("端口:"), 1, 0);
    m_portSpin = new QSpinBox();
    m_portSpin->setRange(1024, 65535);
    m_portSpin->setValue(5555);
    layout->addWidget(m_portSpin, 1, 1, 1, 2);

    // 连接按钮
    m_connectBtn = new QPushButton("开始监听");
    m_connectBtn->setStyleSheet("QPushButton { background-color: #0E639C; color: white; font-weight: bold; padding: 8px; }");
    connect(m_connectBtn, &QPushButton::clicked, this, &SimulatorConfigPanel::onConnectClicked);
    layout->addWidget(m_connectBtn, 2, 0, 1, 3);

    // 状态标签
    m_statusLabel = new QLabel("● 未连接");
    m_statusLabel->setStyleSheet("color: #FF6B6B;");
    layout->addWidget(m_statusLabel, 3, 0, 1, 3);

    // 系统类型标签
    m_systemLabel = new QLabel("系统类型: --");
    m_systemLabel->setStyleSheet("color: #888888; font-size: 10px;");
    layout->addWidget(m_systemLabel, 4, 0, 1, 3);
}

void SimulatorConfigPanel::applyStyles() {
    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

void SimulatorConfigPanel::setConnected(bool connected, const QString& message) {
    m_isConnected = connected;
    if (connected) {
        m_connectBtn->setText("停止监听");
        m_connectBtn->setStyleSheet("QPushButton { background-color: #D32F2F; color: white; font-weight: bold; padding: 8px; }");
        m_statusLabel->setText("● " + (message.isEmpty() ? "已连接" : message));
        m_statusLabel->setStyleSheet("color: #4CAF50;");
    } else {
        m_connectBtn->setText("开始监听");
        m_connectBtn->setStyleSheet("QPushButton { background-color: #0E639C; color: white; font-weight: bold; padding: 8px; }");
        m_statusLabel->setText("● 未连接");
        m_statusLabel->setStyleSheet("color: #FF6B6B;");
    }
}

void SimulatorConfigPanel::setSystemType(const QString& systemType, const QString& version, int stateCount) {
    m_systemLabel->setText(QString("系统: %1 v%2 (%3个状态)").arg(systemType, version).arg(stateCount));
}

void SimulatorConfigPanel::onConnectClicked() {
    if (m_isConnected) {
        emit disconnectRequested();
    } else {
        emit connectRequested(m_hostEdit->text(), m_portSpin->value());
    }
}
