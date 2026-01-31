// RealtimePlotWidget.cpp - 实时绑图组件实现 (简化版)
#include "ui/plots/RealtimePlotWidget.h"
#include <QVBoxLayout>
#include <QHBoxLayout>

const QMap<QString, QString> RealtimePlotWidget::Colors = {
    {"setpoint", "#FF6B6B"}, {"process_value", "#4ECDC4"}, {"error", "#FFE66D"}, {"output", "#95E1D3"}
};

RealtimePlotWidget::RealtimePlotWidget(const QString& title, QWidget* parent) : QWidget(parent), m_title(title), m_maxPoints(1000), m_autoScale(true) {
    setupUi();
}

RealtimePlotWidget::~RealtimePlotWidget() = default;

void RealtimePlotWidget::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);

    // 标题和控制
    QHBoxLayout* titleLayout = new QHBoxLayout();
    m_titleLabel = new QLabel(m_title);
    m_titleLabel->setStyleSheet("color: #4FC3F7; font-weight: bold;");
    titleLayout->addWidget(m_titleLabel);

    m_valueLabel = new QLabel();
    m_valueLabel->setStyleSheet("color: #AAAAAA;");
    titleLayout->addWidget(m_valueLabel);
    titleLayout->addStretch();

    m_autoScaleBtn = new QPushButton("自动缩放");
    m_autoScaleBtn->setCheckable(true);
    m_autoScaleBtn->setChecked(true);
    connect(m_autoScaleBtn, &QPushButton::toggled, this, &RealtimePlotWidget::onAutoScaleClicked);
    titleLayout->addWidget(m_autoScaleBtn);

    m_pointsCombo = new QComboBox();
    m_pointsCombo->addItems({"500", "1000", "2000", "5000"});
    m_pointsCombo->setCurrentText("1000");
    connect(m_pointsCombo, &QComboBox::currentTextChanged, this, &RealtimePlotWidget::onPointsChanged);
    titleLayout->addWidget(m_pointsCombo);

    layout->addLayout(titleLayout);

    // Qt Charts
    m_chart = new QChart();
    m_chart->setBackgroundBrush(QBrush(QColor("#1E1E1E")));
    m_chart->legend()->hide();
    m_chart->setMargins(QMargins(0, 0, 0, 0));

    m_axisX = new QValueAxis();
    m_axisX->setTitleText("时间 (s)");
    m_axisX->setLabelsColor(Qt::white);
    m_axisX->setGridLineColor(QColor("#3D3D3D"));
    m_chart->addAxis(m_axisX, Qt::AlignBottom);

    m_axisY = new QValueAxis();
    m_axisY->setLabelsColor(Qt::white);
    m_axisY->setGridLineColor(QColor("#3D3D3D"));
    m_chart->addAxis(m_axisY, Qt::AlignLeft);

    m_chartView = new QChartView(m_chart);
    m_chartView->setRenderHint(QPainter::Antialiasing);
    m_chartView->setBackgroundBrush(QBrush(QColor("#1E1E1E")));
    layout->addWidget(m_chartView, 1);
}

void RealtimePlotWidget::addCurve(const QString& name, const QString& color, int width) {
    QLineSeries* series = new QLineSeries();
    series->setName(name);
    series->setPen(QPen(QColor(color.isEmpty() ? Colors.value(name, "#FFFFFF") : color), width));
    m_chart->addSeries(series);
    series->attachAxis(m_axisX);
    series->attachAxis(m_axisY);
    m_curves[name] = series;
}

void RealtimePlotWidget::updateCurve(const QString& name, const QVector<double>& x, const QVector<double>& y) {
    if (!m_curves.contains(name)) return;
    QLineSeries* series = m_curves[name];
    series->clear();
    for (int i = 0; i < qMin(x.size(), y.size()); ++i) {
        series->append(x[i], y[i]);
    }
    if (!x.isEmpty() && !y.isEmpty()) {
        m_latestValues[name] = y.last();
        if (m_autoScale) {
            m_axisX->setRange(x.first(), x.last());
            double minY = *std::min_element(y.begin(), y.end());
            double maxY = *std::max_element(y.begin(), y.end());
            double padding = (maxY - minY) * 0.1;
            m_axisY->setRange(minY - padding, maxY + padding);
        }
    }
    updateValueDisplay();
}

void RealtimePlotWidget::clearCurves() {
    for (auto* series : m_curves) series->clear();
    m_latestValues.clear();
}

void RealtimePlotWidget::setYLabel(const QString& label, const QString& units) { m_axisY->setTitleText(label + (units.isEmpty() ? "" : " (" + units + ")")); }
void RealtimePlotWidget::setXRange(double min, double max) { m_axisX->setRange(min, max); }
void RealtimePlotWidget::setYRange(double min, double max) { m_axisY->setRange(min, max); }
void RealtimePlotWidget::enableAutoRange(bool enable) { m_autoScale = enable; m_autoScaleBtn->setChecked(enable); }
void RealtimePlotWidget::onAutoScaleClicked(bool checked) { m_autoScale = checked; emit autoScaleToggled(checked); }
void RealtimePlotWidget::onPointsChanged(const QString& text) { m_maxPoints = text.toInt(); }
void RealtimePlotWidget::updateValueDisplay() {
    QStringList parts;
    for (auto it = m_latestValues.begin(); it != m_latestValues.end(); ++it) {
        parts << QString("%1: %2").arg(it.key()).arg(it.value(), 0, 'f', 2);
    }
    m_valueLabel->setText(parts.join(" | "));
}
