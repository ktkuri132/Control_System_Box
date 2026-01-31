/**
 * DialWithLabel.cpp - 带标签的旋钮控件实现
 */

#include "ui/widgets/DialWithLabel.h"

#include <QVBoxLayout>

DialWithLabel::DialWithLabel(const QString& label, double minVal, double maxVal, double defaultVal, int decimals, QWidget* parent)
    : QWidget(parent)
    , m_decimals(decimals)
    , m_min(minVal)
    , m_max(maxVal)
{
    m_scale = qPow(10, decimals);
    setupUi(label);
    setValue(defaultVal);
}

void DialWithLabel::setupUi(const QString& label) {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(2, 2, 2, 2);
    layout->setSpacing(2);

    // 标签
    m_label = new QLabel(label);
    m_label->setAlignment(Qt::AlignCenter);
    m_label->setStyleSheet("color: #4FC3F7; font-weight: bold;");
    layout->addWidget(m_label);

    // 旋钮
    m_dial = new QDial();
    m_dial->setRange(static_cast<int>(m_min * m_scale), static_cast<int>(m_max * m_scale));
    m_dial->setNotchesVisible(true);
    m_dial->setFixedSize(60, 60);
    m_dial->setStyleSheet("QDial { background-color: #3C3C3C; }");
    connect(m_dial, &QDial::valueChanged, this, &DialWithLabel::onDialChanged);
    layout->addWidget(m_dial, 0, Qt::AlignCenter);

    // 数值输入框
    m_spinbox = new QDoubleSpinBox();
    m_spinbox->setRange(m_min, m_max);
    m_spinbox->setDecimals(m_decimals);
    m_spinbox->setSingleStep(1.0 / m_scale);
    m_spinbox->setAlignment(Qt::AlignCenter);
    m_spinbox->setStyleSheet("QDoubleSpinBox { background-color: #3C3C3C; color: white; border: 1px solid #555555; }");
    connect(m_spinbox, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &DialWithLabel::onSpinboxChanged);
    layout->addWidget(m_spinbox);
}

double DialWithLabel::value() const {
    return m_spinbox->value();
}

void DialWithLabel::setValue(double value) {
    m_spinbox->blockSignals(true);
    m_dial->blockSignals(true);

    m_spinbox->setValue(value);
    m_dial->setValue(static_cast<int>(value * m_scale));

    m_spinbox->blockSignals(false);
    m_dial->blockSignals(false);
}

void DialWithLabel::setRange(double min, double max) {
    m_min = min;
    m_max = max;
    m_dial->setRange(static_cast<int>(min * m_scale), static_cast<int>(max * m_scale));
    m_spinbox->setRange(min, max);
}

void DialWithLabel::onDialChanged(int value) {
    double dval = value / m_scale;
    m_spinbox->blockSignals(true);
    m_spinbox->setValue(dval);
    m_spinbox->blockSignals(false);
    emit valueChanged(dval);
}

void DialWithLabel::onSpinboxChanged(double value) {
    m_dial->blockSignals(true);
    m_dial->setValue(static_cast<int>(value * m_scale));
    m_dial->blockSignals(false);
    emit valueChanged(value);
}
