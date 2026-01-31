/**
 * SerialConfigPanel.cpp - 串口配置面板实现
 */

#include "ui/panels/SerialConfigPanel.h"
#include "core/SerialManager.h"

#include <QGridLayout>
#include <QLabel>

SerialConfigPanel::SerialConfigPanel(QWidget* parent)
    : QGroupBox("串口配置", parent)
{
    setupUi();
    applyStyles();
}

void SerialConfigPanel::setupUi() {
    QGridLayout* layout = new QGridLayout(this);
    layout->setSpacing(8);

    // 端口选择
    layout->addWidget(new QLabel("端口:"), 0, 0);
    m_portCombo = new QComboBox();
    m_portCombo->setMinimumWidth(120);
    layout->addWidget(m_portCombo, 0, 1);

    m_refreshBtn = new QPushButton("🔄");
    m_refreshBtn->setFixedWidth(30);
    m_refreshBtn->setToolTip("刷新串口列表");
    connect(m_refreshBtn, &QPushButton::clicked, this, &SerialConfigPanel::refreshPorts);
    layout->addWidget(m_refreshBtn, 0, 2);

    // 波特率选择
    layout->addWidget(new QLabel("波特率:"), 1, 0);
    m_baudrateCombo = new QComboBox();
    m_baudrateCombo->addItems({"9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"});
    m_baudrateCombo->setCurrentText("115200");
    layout->addWidget(m_baudrateCombo, 1, 1, 1, 2);

    // 连接按钮
    m_connectBtn = new QPushButton("连接");
    m_connectBtn->setStyleSheet("QPushButton { background-color: #0E639C; color: white; font-weight: bold; padding: 8px; }");
    connect(m_connectBtn, &QPushButton::clicked, this, &SerialConfigPanel::onConnectClicked);
    layout->addWidget(m_connectBtn, 2, 0, 1, 3);

    // 状态标签
    m_statusLabel = new QLabel("● 未连接");
    m_statusLabel->setStyleSheet("color: #FF6B6B;");
    layout->addWidget(m_statusLabel, 3, 0, 1, 3);
}

void SerialConfigPanel::applyStyles() {
    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

void SerialConfigPanel::refreshPorts() {
    m_portCombo->clear();
    auto ports = SerialManager::getAvailablePorts();
    for (const auto& port : ports) {
        m_portCombo->addItem(port.second, port.first);
    }
}

void SerialConfigPanel::setConnected(bool connected) {
    m_isConnected = connected;
    if (connected) {
        m_connectBtn->setText("断开");
        m_connectBtn->setStyleSheet("QPushButton { background-color: #D32F2F; color: white; font-weight: bold; padding: 8px; }");
        m_statusLabel->setText("● 已连接");
        m_statusLabel->setStyleSheet("color: #4CAF50;");
    } else {
        m_connectBtn->setText("连接");
        m_connectBtn->setStyleSheet("QPushButton { background-color: #0E639C; color: white; font-weight: bold; padding: 8px; }");
        m_statusLabel->setText("● 未连接");
        m_statusLabel->setStyleSheet("color: #FF6B6B;");
    }
}

void SerialConfigPanel::onConnectClicked() {
    if (m_isConnected) {
        emit disconnectRequested();
    } else {
        QString port = m_portCombo->currentData().toString();
        int baudrate = m_baudrateCombo->currentText().toInt();
        emit connectRequested(port, baudrate);
    }
}
