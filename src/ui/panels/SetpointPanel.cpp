/**
 * SetpointPanel.cpp - 设定值控制面板实现
 */

#include "ui/panels/SetpointPanel.h"
#include "ui/widgets/SliderWithLabel.h"

#include <QVBoxLayout>

SetpointPanel::SetpointPanel(QWidget* parent)
    : QGroupBox("设定值 (Setpoint)", parent)
{
    setupUi();
}

void SetpointPanel::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setSpacing(8);

    m_spSlider = new SliderWithLabel("SP", 0.0, 100.0, 50.0, 1);
    connect(m_spSlider, &SliderWithLabel::valueChanged, this, &SetpointPanel::onValueChanged);
    layout->addWidget(m_spSlider);

    m_sendBtn = new QPushButton("发送设定值");
    m_sendBtn->setStyleSheet("QPushButton { background-color: #1976D2; color: white; padding: 6px; }");
    connect(m_sendBtn, &QPushButton::clicked, this, &SetpointPanel::onSendClicked);
    layout->addWidget(m_sendBtn);

    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

double SetpointPanel::getValue() const {
    return m_spSlider->value();
}

void SetpointPanel::setValue(double value) {
    m_spSlider->setValue(value);
}

void SetpointPanel::onValueChanged(double value) {
    emit setpointChanged(value);
}

void SetpointPanel::onSendClicked() {
    emit sendRequested(m_spSlider->value());
}
