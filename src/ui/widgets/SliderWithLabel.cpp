/**
 * SliderWithLabel.cpp - 带标签的滑块控件实现
 */

#include "ui/widgets/SliderWithLabel.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QtMath>

SliderWithLabel::SliderWithLabel(const QString& label, double minVal, double maxVal, double defaultVal, int decimals, QWidget* parent)
    : QWidget(parent)
    , m_decimals(decimals)
{
    m_scale = qPow(10, decimals);
    setupUi(label);

    m_slider->setRange(static_cast<int>(minVal * m_scale), static_cast<int>(maxVal * m_scale));
    m_spinbox->setRange(minVal, maxVal);
    m_spinbox->setDecimals(decimals);
    m_spinbox->setSingleStep(1.0 / m_scale);

    setValue(defaultVal);
}

void SliderWithLabel::setupUi(const QString& label) {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(2);

    // 标签
    m_label = new QLabel(label);
    m_label->setStyleSheet("color: #4FC3F7; font-weight: bold;");
    layout->addWidget(m_label);

    // 滑块和数值行
    QHBoxLayout* sliderLayout = new QHBoxLayout();

    m_slider = new QSlider(Qt::Horizontal);
    connect(m_slider, &QSlider::valueChanged, this, &SliderWithLabel::onSliderChanged);
    sliderLayout->addWidget(m_slider, 1);

    m_spinbox = new QDoubleSpinBox();
    m_spinbox->setFixedWidth(70);
    m_spinbox->setAlignment(Qt::AlignCenter);
    m_spinbox->setStyleSheet("QDoubleSpinBox { background-color: #3C3C3C; color: white; border: 1px solid #555555; }");
    connect(m_spinbox, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &SliderWithLabel::onSpinboxChanged);
    sliderLayout->addWidget(m_spinbox);

    layout->addLayout(sliderLayout);
}

double SliderWithLabel::value() const {
    return m_spinbox->value();
}

void SliderWithLabel::setValue(double value) {
    m_spinbox->blockSignals(true);
    m_slider->blockSignals(true);

    m_spinbox->setValue(value);
    m_slider->setValue(static_cast<int>(value * m_scale));

    m_spinbox->blockSignals(false);
    m_slider->blockSignals(false);
}

void SliderWithLabel::setRange(double min, double max) {
    m_slider->setRange(static_cast<int>(min * m_scale), static_cast<int>(max * m_scale));
    m_spinbox->setRange(min, max);
}

void SliderWithLabel::onSliderChanged(int value) {
    double dval = value / m_scale;
    m_spinbox->blockSignals(true);
    m_spinbox->setValue(dval);
    m_spinbox->blockSignals(false);
    emit valueChanged(dval);
}

void SliderWithLabel::onSpinboxChanged(double value) {
    m_slider->blockSignals(true);
    m_slider->setValue(static_cast<int>(value * m_scale));
    m_slider->blockSignals(false);
    emit valueChanged(value);
}
