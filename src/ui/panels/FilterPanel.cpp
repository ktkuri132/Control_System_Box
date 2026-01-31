/**
 * FilterPanel.cpp - 滤波控制面板实现
 */

#include "ui/panels/FilterPanel.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QHeaderView>

FilterPanel::FilterPanel(QWidget* parent)
    : QWidget(parent)
{
    setupUi();
}

void FilterPanel::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);
    layout->setSpacing(5);

    // 滤波设置组
    m_filterGroup = new QGroupBox("信号滤波");
    m_filterGroup->setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #4FC3F7; }
    )");

    QVBoxLayout* filterLayout = new QVBoxLayout(m_filterGroup);

    m_enableCheck = new QCheckBox("启用滤波");
    connect(m_enableCheck, &QCheckBox::stateChanged, this, &FilterPanel::onEnableChanged);
    filterLayout->addWidget(m_enableCheck);

    // 算法选择
    QHBoxLayout* algoLayout = new QHBoxLayout();
    QLabel* algoLabel = new QLabel("算法:");
    algoLabel->setStyleSheet("color: #AAAAAA;");
    m_algoCombo = new QComboBox();
    m_algoCombo->addItems({"移动平均", "指数平滑", "低通滤波", "中值滤波", "卡尔曼滤波", "融合滤波"});
    m_algoCombo->setEnabled(false);
    connect(m_algoCombo, &QComboBox::currentTextChanged, this, &FilterPanel::onAlgoChanged);
    algoLayout->addWidget(algoLabel);
    algoLayout->addWidget(m_algoCombo, 1);
    filterLayout->addLayout(algoLayout);

    // 强度滑块
    QHBoxLayout* strengthLayout = new QHBoxLayout();
    QLabel* strengthLabel = new QLabel("强度:");
    strengthLabel->setStyleSheet("color: #AAAAAA;");
    m_strengthSlider = new QSlider(Qt::Horizontal);
    m_strengthSlider->setRange(1, 10);
    m_strengthSlider->setValue(5);
    m_strengthSlider->setEnabled(false);
    connect(m_strengthSlider, &QSlider::valueChanged, this, &FilterPanel::onStrengthChanged);
    m_strengthValue = new QLabel("5");
    m_strengthValue->setStyleSheet("color: #4FC3F7; min-width: 20px;");
    strengthLayout->addWidget(strengthLabel);
    strengthLayout->addWidget(m_strengthSlider, 1);
    strengthLayout->addWidget(m_strengthValue);
    filterLayout->addLayout(strengthLayout);

    // 算法描述
    m_algoDesc = new QLabel("移动平均: 平滑噪声，响应较慢");
    m_algoDesc->setWordWrap(true);
    m_algoDesc->setStyleSheet("color: #888888; font-size: 10px;");
    filterLayout->addWidget(m_algoDesc);

    layout->addWidget(m_filterGroup);

    // 谐波分析组
    m_harmonicGroup = new QGroupBox("谐波分析");
    m_harmonicGroup->setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #81C784; }
    )");

    QVBoxLayout* harmonicLayout = new QVBoxLayout(m_harmonicGroup);

    // THD显示
    QHBoxLayout* thdLayout = new QHBoxLayout();
    QLabel* thdLabel = new QLabel("总谐波失真(THD):");
    thdLabel->setStyleSheet("color: #AAAAAA;");
    m_thdValue = new QLabel("--");
    m_thdValue->setStyleSheet("color: #FF9800; font-weight: bold;");
    thdLayout->addWidget(thdLabel);
    thdLayout->addWidget(m_thdValue);
    harmonicLayout->addLayout(thdLayout);

    // 基频显示
    QHBoxLayout* fundLayout = new QHBoxLayout();
    QLabel* fundLabel = new QLabel("基频:");
    fundLabel->setStyleSheet("color: #AAAAAA;");
    m_fundValue = new QLabel("--");
    m_fundValue->setStyleSheet("color: #4FC3F7;");
    fundLayout->addWidget(fundLabel);
    fundLayout->addWidget(m_fundValue);
    harmonicLayout->addLayout(fundLayout);

    // 谐波表格
    m_harmonicTable = new QTableWidget(5, 4);
    m_harmonicTable->setHorizontalHeaderLabels({"次数", "频率", "幅值", "相位"});
    m_harmonicTable->setMaximumHeight(120);
    m_harmonicTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_harmonicTable->setStyleSheet(R"(
        QTableWidget { background-color: #2D2D30; color: #CCCCCC; border: 1px solid #3D3D3D; gridline-color: #3D3D3D; }
        QHeaderView::section { background-color: #3C3C3C; color: #FFFFFF; padding: 4px; }
    )");
    harmonicLayout->addWidget(m_harmonicTable);

    layout->addWidget(m_harmonicGroup);
    layout->addStretch();
}

void FilterPanel::onEnableChanged(int state) {
    bool enabled = (state == Qt::Checked);
    setControlsEnabled(enabled);
    emit filterChanged();
}

void FilterPanel::onAlgoChanged(const QString& text) {
    updateAlgoDescription();
    emit filterChanged();
}

void FilterPanel::onStrengthChanged(int value) {
    m_strengthValue->setText(QString::number(value));
    emit filterChanged();
}

void FilterPanel::setControlsEnabled(bool enabled) {
    m_algoCombo->setEnabled(enabled);
    m_strengthSlider->setEnabled(enabled);
}

void FilterPanel::updateAlgoDescription() {
    QString algo = m_algoCombo->currentText();
    QString desc;

    if (algo == "移动平均") desc = "移动平均: 平滑噪声，响应较慢";
    else if (algo == "指数平滑") desc = "指数平滑: 平滑噪声，响应较快";
    else if (algo == "低通滤波") desc = "低通滤波: 滤除高频噪声";
    else if (algo == "中值滤波") desc = "中值滤波: 去除脉冲噪声";
    else if (algo == "卡尔曼滤波") desc = "卡尔曼滤波: 最优估计，需要模型";
    else if (algo == "融合滤波") desc = "融合滤波: 多种滤波算法融合";

    m_algoDesc->setText(desc);
}

void FilterPanel::updateHarmonicAnalysis(const HarmonicAnalysis& analysis) {
    m_thdValue->setText(QString::number(analysis.thd, 'f', 2) + "%");
    m_fundValue->setText(QString::number(analysis.fundamentalFreq, 'f', 2) + " Hz");

    int rows = qMin(5, analysis.harmonicFreqs.size());
    for (int i = 0; i < rows; ++i) {
        m_harmonicTable->setItem(i, 0, new QTableWidgetItem(QString::number(i + 1)));
        m_harmonicTable->setItem(i, 1, new QTableWidgetItem(QString::number(analysis.harmonicFreqs[i], 'f', 2)));
        m_harmonicTable->setItem(i, 2, new QTableWidgetItem(QString::number(analysis.harmonicMags[i], 'f', 4)));
        m_harmonicTable->setItem(i, 3, new QTableWidgetItem(QString::number(analysis.harmonicPhases[i], 'f', 1) + "°"));
    }
}
