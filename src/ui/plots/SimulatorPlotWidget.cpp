// SimulatorPlotWidget.cpp - 仿真数据绘图组件实现
#include "ui/plots/SimulatorPlotWidget.h"
#include "ui/plots/RealtimePlotWidget.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>

SimulatorPlotWidget::SimulatorPlotWidget(QWidget* parent) : QWidget(parent) { setupUi(); }
SimulatorPlotWidget::~SimulatorPlotWidget() = default;

void SimulatorPlotWidget::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);

    // 状态选择
    QHBoxLayout* headerLayout = new QHBoxLayout();
    QLabel* stateLabel = new QLabel("状态变量:");
    stateLabel->setStyleSheet("color: #AAAAAA;");
    headerLayout->addWidget(stateLabel);

    m_stateCombo = new QComboBox();
    m_stateCombo->setMinimumWidth(150);
    connect(m_stateCombo, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &SimulatorPlotWidget::onStateSelected);
    headerLayout->addWidget(m_stateCombo);

    m_stateInfoLabel = new QLabel();
    m_stateInfoLabel->setStyleSheet("color: #888888; font-size: 10px;");
    headerLayout->addWidget(m_stateInfoLabel);

    headerLayout->addStretch();

    m_systemLabel = new QLabel("系统: --");
    m_systemLabel->setStyleSheet("color: #81C784;");
    headerLayout->addWidget(m_systemLabel);

    layout->addLayout(headerLayout);

    // 标准响应图
    m_standardPlot = new StandardResponseWidget(this);
    layout->addWidget(m_standardPlot, 1);
}

void SimulatorPlotWidget::setStateDefinitions(const QList<StateDefinition>& stateDefs) {
    m_stateDefs = stateDefs;
    m_stateCombo->clear();
    for (const auto& def : stateDefs) {
        QString text = def.name;
        if (!def.unit.isEmpty()) text += " (" + def.unit + ")";
        m_stateCombo->addItem(text, def.index);
    }
    if (!stateDefs.isEmpty()) onStateSelected(0);
}

void SimulatorPlotWidget::onStateSelected(int index) {
    if (index < 0 || index >= m_stateDefs.size()) return;
    m_selectedStateIndex = index;
    const auto& def = m_stateDefs[index];
    m_stateInfoLabel->setText(def.description.isEmpty() ? "" : def.description);
    emit stateSelectionChanged(index);
}

void SimulatorPlotWidget::setSystemType(const QString& systemType) {
    m_currentSystem = systemType;
    m_systemLabel->setText("系统: " + systemType);
}

void SimulatorPlotWidget::clearAll() { m_standardPlot->clearAll(); }
void SimulatorPlotWidget::clearStateDefinitions() { m_stateDefs.clear(); m_stateCombo->clear(); m_systemLabel->setText("系统: --"); }

// StandardResponseWidget
StandardResponseWidget::StandardResponseWidget(QWidget* parent) : QWidget(parent) { setupUi(); }
StandardResponseWidget::~StandardResponseWidget() = default;

void StandardResponseWidget::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    m_responsePlot = new RealtimePlotWidget("响应曲线");
    m_responsePlot->addCurve("setpoint", "#FF6B6B", 2);
    m_responsePlot->addCurve("process_value", "#4ECDC4", 2);
    m_responsePlot->setYLabel("数值");
    layout->addWidget(m_responsePlot);
}

void StandardResponseWidget::updateData(const QVector<double>& timestamps, const QVector<double>& setpoints,
    const QVector<double>& processValues, const QVector<double>& errors, const QVector<double>& outputs, const QVector<double>& rawValues) {
    m_responsePlot->updateCurve("setpoint", timestamps, setpoints);
    m_responsePlot->updateCurve("process_value", timestamps, processValues);
}

void StandardResponseWidget::updateFFT(const QVector<double>& frequencies, const QVector<double>& magnitudes) {}
void StandardResponseWidget::setShowRaw(bool show) { m_showRaw = show; }
void StandardResponseWidget::clearAll() { m_responsePlot->clearCurves(); }
void StandardResponseWidget::openAnalysisWindow() {}
void StandardResponseWidget::openExtendedWindow() {}
