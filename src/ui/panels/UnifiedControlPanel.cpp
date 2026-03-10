/**
 * UnifiedControlPanel.cpp - 统一控制面板实现
 */

#include "ui/panels/UnifiedControlPanel.h"
#include "ui/panels/SerialConfigPanel.h"
#include "ui/panels/SimulatorConfigPanel.h"
#include "ui/panels/SetpointPanel.h"
#include "ui/panels/PIDControlPanel.h"
#include "ui/panels/MetricsPanel.h"
#include "ui/panels/DataControlPanel.h"
#include "ui/panels/FilterPanel.h"

#include <QVBoxLayout>
#include <QScrollArea>

UnifiedControlPanel::UnifiedControlPanel(QWidget* parent)
    : QWidget(parent)
{
    setupUi();
}

UnifiedControlPanel::~UnifiedControlPanel() = default;

void UnifiedControlPanel::setupUi() {
    setFixedWidth(280);

    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(5);

    QScrollArea* scrollArea = new QScrollArea(this);
    scrollArea->setWidgetResizable(true);
    scrollArea->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scrollArea->setStyleSheet("QScrollArea { border: none; background: transparent; }");

    QWidget* container = new QWidget();
    QVBoxLayout* containerLayout = new QVBoxLayout(container);
    containerLayout->setContentsMargins(5, 5, 5, 5);
    containerLayout->setSpacing(10);

    // 连接配置堆栈
    m_connectionStack = new QStackedWidget();
    m_serialPanel = new SerialConfigPanel();
    m_simulatorPanel = new SimulatorConfigPanel();
    m_connectionStack->addWidget(m_serialPanel);
    m_connectionStack->addWidget(m_simulatorPanel);
    containerLayout->addWidget(m_connectionStack);

    // 设定值面板
    m_setpointPanel = new SetpointPanel();
    containerLayout->addWidget(m_setpointPanel);

    // PID控制面板
    m_pidPanel = new PIDControlPanel();
    containerLayout->addWidget(m_pidPanel);

    // 性能指标面板
    m_metricsPanel = new MetricsPanel();
    containerLayout->addWidget(m_metricsPanel);

    // 数据控制面板
    m_dataPanel = new DataControlPanel();
    containerLayout->addWidget(m_dataPanel);

    // 滤波面板
    m_filterPanel = new FilterPanel();
    containerLayout->addWidget(m_filterPanel);

    containerLayout->addStretch();

    scrollArea->setWidget(container);
    mainLayout->addWidget(scrollArea);
}

void UnifiedControlPanel::setMode(int mode) {
    m_connectionStack->setCurrentIndex(mode);
}
