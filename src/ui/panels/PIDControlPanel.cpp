/**
 * PIDControlPanel.cpp - PID参数控制面板实现
 */

#include "ui/panels/PIDControlPanel.h"
#include "ui/widgets/DialWithLabel.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFrame>

PIDControlPanel::PIDControlPanel(QWidget* parent)
    : QGroupBox("PID 参数调节", parent)
{
    setupUi();
    applyStyles();
}

void PIDControlPanel::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setSpacing(10);

    // 旋钮行
    QHBoxLayout* dialLayout = new QHBoxLayout();
    dialLayout->setSpacing(5);

    m_kpDial = new DialWithLabel("Kp", 0.0, 100.0, 1.0, 2);
    m_kiDial = new DialWithLabel("Ki", 0.0, 10.0, 0.0, 3);
    m_kdDial = new DialWithLabel("Kd", 0.0, 10.0, 0.0, 3);

    connect(m_kpDial, &DialWithLabel::valueChanged, this, &PIDControlPanel::onValueChanged);
    connect(m_kiDial, &DialWithLabel::valueChanged, this, &PIDControlPanel::onValueChanged);
    connect(m_kdDial, &DialWithLabel::valueChanged, this, &PIDControlPanel::onValueChanged);

    dialLayout->addWidget(m_kpDial);
    dialLayout->addWidget(m_kiDial);
    dialLayout->addWidget(m_kdDial);
    layout->addLayout(dialLayout);

    // 分隔线
    QFrame* line = new QFrame();
    line->setFrameShape(QFrame::HLine);
    line->setStyleSheet("background-color: #3D3D3D;");
    layout->addWidget(line);

    // 实时发送复选框
    m_realtimeCheck = new QCheckBox("实时发送");
    connect(m_realtimeCheck, &QCheckBox::toggled, this, &PIDControlPanel::onRealtimeToggled);
    layout->addWidget(m_realtimeCheck);

    // 发送按钮
    m_sendBtn = new QPushButton("发送 PID 参数");
    m_sendBtn->setStyleSheet("QPushButton { background-color: #388E3C; color: white; font-weight: bold; padding: 10px; }");
    connect(m_sendBtn, &QPushButton::clicked, this, &PIDControlPanel::onSendClicked);
    layout->addWidget(m_sendBtn);

    // 参数显示标签
    m_paramsLabel = new QLabel("Kp=1.00, Ki=0.000, Kd=0.000");
    m_paramsLabel->setAlignment(Qt::AlignCenter);
    m_paramsLabel->setStyleSheet("color: #888888; font-size: 10px;");
    layout->addWidget(m_paramsLabel);
}

void PIDControlPanel::applyStyles() {
    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

void PIDControlPanel::getValues(double& kp, double& ki, double& kd) const {
    kp = m_kpDial->value();
    ki = m_kiDial->value();
    kd = m_kdDial->value();
}

void PIDControlPanel::setValues(double kp, double ki, double kd) {
    m_kpDial->setValue(kp);
    m_kiDial->setValue(ki);
    m_kdDial->setValue(kd);
}

void PIDControlPanel::onValueChanged() {
    double kp = m_kpDial->value();
    double ki = m_kiDial->value();
    double kd = m_kdDial->value();

    m_paramsLabel->setText(QString("Kp=%1, Ki=%2, Kd=%3")
        .arg(kp, 0, 'f', 2)
        .arg(ki, 0, 'f', 3)
        .arg(kd, 0, 'f', 3));

    emit pidChanged(kp, ki, kd);

    if (m_realtimeSend) {
        emit sendRequested(kp, ki, kd);
    }
}

void PIDControlPanel::onRealtimeToggled(bool checked) {
    m_realtimeSend = checked;
}

void PIDControlPanel::onSendClicked() {
    double kp, ki, kd;
    getValues(kp, ki, kd);
    emit sendRequested(kp, ki, kd);
}
