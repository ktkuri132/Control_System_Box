// MetricCard.cpp - 性能指标卡片实现 (存根)
#include "ui/widgets/MetricCard.h"
#include <QVBoxLayout>

MetricCard::MetricCard(const QString& title, const QString& unit, QWidget* parent) : QFrame(parent), m_unit(unit) {
    setupUi(title, unit);
}

void MetricCard::setupUi(const QString& title, const QString& unit) {
    setStyleSheet("QFrame { background-color: #2D2D30; border: 1px solid #3D3D3D; border-radius: 5px; padding: 5px; }");
    QVBoxLayout* layout = new QVBoxLayout(this);
    m_titleLabel = new QLabel(title);
    m_titleLabel->setStyleSheet("color: #AAAAAA; font-size: 10px;");
    m_valueLabel = new QLabel("--");
    m_valueLabel->setStyleSheet("color: #4FC3F7; font-size: 14px; font-weight: bold;");
    m_statusLabel = new QLabel();
    layout->addWidget(m_titleLabel);
    layout->addWidget(m_valueLabel);
    layout->addWidget(m_statusLabel);
}

void MetricCard::setValue(double value, const QString& statusColor, const QString& statusText) {
    m_valueLabel->setText(QString::number(value, 'f', 3) + " " + m_unit);
    if (!statusText.isEmpty()) m_statusLabel->setText(statusText);
    if (!statusColor.isEmpty()) m_valueLabel->setStyleSheet(QString("color: %1; font-size: 14px; font-weight: bold;").arg(statusColor));
}

void MetricCard::setValue(const QString& text, const QString& statusColor) {
    m_valueLabel->setText(text);
    if (!statusColor.isEmpty()) m_valueLabel->setStyleSheet(QString("color: %1; font-size: 14px; font-weight: bold;").arg(statusColor));
}

void MetricCard::clear() { m_valueLabel->setText("--"); m_statusLabel->clear(); }
