// StabilityGauge.cpp - 稳定性评估仪表盘实现 (存根)
#include "ui/widgets/StabilityGauge.h"
#include <QVBoxLayout>

StabilityGauge::StabilityGauge(QWidget* parent) : QWidget(parent) { setupUi(); }

void StabilityGauge::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    m_titleLabel = new QLabel("稳定性评分");
    m_titleLabel->setStyleSheet("color: #AAAAAA;");
    m_scoreLabel = new QLabel("--");
    m_scoreLabel->setStyleSheet("color: #4ECDC4; font-size: 24px; font-weight: bold;");
    m_progressBar = new QProgressBar();
    m_progressBar->setRange(0, 100);
    m_progressBar->setValue(0);
    m_statusLabel = new QLabel("等待数据...");
    m_statusLabel->setStyleSheet("color: #888888;");
    layout->addWidget(m_titleLabel);
    layout->addWidget(m_scoreLabel);
    layout->addWidget(m_progressBar);
    layout->addWidget(m_statusLabel);
}

void StabilityGauge::setScore(double score, const QString& status) {
    m_scoreLabel->setText(QString::number(score, 'f', 1));
    m_progressBar->setValue(static_cast<int>(score));
    m_statusLabel->setText(status);
    updateColors(score);
}

void StabilityGauge::updateColors(double score) {
    QString color = score >= 80 ? "#4CAF50" : (score >= 50 ? "#FF9800" : "#F44336");
    m_scoreLabel->setStyleSheet(QString("color: %1; font-size: 24px; font-weight: bold;").arg(color));
}

void StabilityGauge::clear() { m_scoreLabel->setText("--"); m_progressBar->setValue(0); m_statusLabel->setText("等待数据..."); }
