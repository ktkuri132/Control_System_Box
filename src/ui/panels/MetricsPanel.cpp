/**
 * MetricsPanel.cpp - 性能指标面板实现
 */

#include "ui/panels/MetricsPanel.h"
#include "core/PerformanceAnalyzer.h"

#include <QVBoxLayout>
#include <QGridLayout>

MetricsPanel::MetricsPanel(QWidget* parent)
    : QGroupBox("性能指标", parent)
{
    setupUi();
    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

void MetricsPanel::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);

    m_stack = new QStackedWidget();

    // 串口模式指标
    QVector<std::tuple<QString, QString, QString>> serialConfig = {
        {"rise_time", "上升时间", "s"},
        {"settling_time", "调节时间", "s"},
        {"overshoot", "超调量", "%"},
        {"peak_time", "峰值时间", "s"},
        {"steady_state_error", "稳态误差", ""},
        {"oscillation_count", "振荡次数", ""},
        {"rms_error", "RMS误差", ""},
        {"iae", "IAE", ""}
    };
    m_stack->addWidget(createMetricsGrid(serialConfig));

    // 倒立摆指标
    QVector<std::tuple<QString, QString, QString>> pendulumConfig = {
        {"angle", "当前角度", "°"},
        {"cart_pos", "小车位置", "m"},
        {"force", "控制力", "N"},
        {"max_angle", "最大偏角", "°"},
        {"angular_vel", "角速度", "°/s"},
        {"settling", "稳定性", ""}
    };
    m_stack->addWidget(createMetricsGrid(pendulumConfig));

    // 滚球系统指标
    QVector<std::tuple<QString, QString, QString>> ballConfig = {
        {"error", "位置误差", "mm"},
        {"ball_pos", "小球位置", ""},
        {"plate_angle", "平板角度", "°"},
        {"max_error", "最大误差", "mm"},
        {"track_error", "跟踪误差", "mm"},
        {"settling", "稳定性", ""}
    };
    m_stack->addWidget(createMetricsGrid(ballConfig));

    layout->addWidget(m_stack);
}

QWidget* MetricsPanel::createMetricsGrid(const QVector<std::tuple<QString, QString, QString>>& config) {
    QWidget* widget = new QWidget();
    QGridLayout* layout = new QGridLayout(widget);
    layout->setSpacing(5);

    int row = 0;
    for (const auto& [key, name, unit] : config) {
        QLabel* nameLabel = new QLabel(name + ":");
        nameLabel->setStyleSheet("color: #AAAAAA; font-size: 11px;");

        QLabel* valueLabel = new QLabel("--");
        valueLabel->setStyleSheet("color: #4FC3F7; font-weight: bold;");
        valueLabel->setAlignment(Qt::AlignRight);

        m_metrics[key] = valueLabel;

        layout->addWidget(nameLabel, row, 0);
        layout->addWidget(valueLabel, row, 1);
        row++;
    }

    return widget;
}

void MetricsPanel::setMode(int mode) {
    m_currentMode = mode;
    m_stack->setCurrentIndex(mode);
}

void MetricsPanel::updateSerialMetrics(const PerformanceMetrics& metrics) {
    auto setValue = [this](const QString& key, std::optional<double> value, const QString& format = "%.3f") {
        if (m_metrics.contains(key)) {
            if (value.has_value()) {
                m_metrics[key]->setText(QString::asprintf(format.toUtf8().constData(), *value));
            } else {
                m_metrics[key]->setText("--");
            }
        }
    };

    setValue("rise_time", metrics.riseTime, "%.3f s");
    setValue("settling_time", metrics.settlingTime, "%.3f s");
    setValue("overshoot", metrics.overshoot, "%.2f %%");
    setValue("peak_time", metrics.peakTime, "%.3f s");
    setValue("steady_state_error", metrics.steadyStateError, "%.4f");

    if (m_metrics.contains("oscillation_count")) {
        m_metrics["oscillation_count"]->setText(QString::number(metrics.oscillationCount));
    }

    setValue("rms_error", metrics.rmsError, "%.4f");
    setValue("iae", metrics.iae, "%.4f");
}

void MetricsPanel::updatePendulumMetrics(double angle, double cartPos, double force, double maxAngle, double angularVel, const QString& settling) {
    if (m_metrics.contains("angle")) m_metrics["angle"]->setText(QString::number(angle, 'f', 2) + "°");
    if (m_metrics.contains("cart_pos")) m_metrics["cart_pos"]->setText(QString::number(cartPos, 'f', 3) + " m");
    if (m_metrics.contains("force")) m_metrics["force"]->setText(QString::number(force, 'f', 2) + " N");
    if (m_metrics.contains("max_angle")) m_metrics["max_angle"]->setText(QString::number(maxAngle, 'f', 2) + "°");
    if (m_metrics.contains("angular_vel")) m_metrics["angular_vel"]->setText(QString::number(angularVel, 'f', 2) + "°/s");
    if (m_metrics.contains("settling")) m_metrics["settling"]->setText(settling);
}

void MetricsPanel::updateBallMetrics(double error, double ballX, double ballY, double plateX, double plateY, double maxError, double trackError, const QString& settling) {
    if (m_metrics.contains("error")) m_metrics["error"]->setText(QString::number(error, 'f', 2) + " mm");
    if (m_metrics.contains("ball_pos")) m_metrics["ball_pos"]->setText(QString("(%1, %2)").arg(ballX, 0, 'f', 1).arg(ballY, 0, 'f', 1));
    if (m_metrics.contains("plate_angle")) m_metrics["plate_angle"]->setText(QString("(%1, %2)°").arg(plateX, 0, 'f', 1).arg(plateY, 0, 'f', 1));
    if (m_metrics.contains("max_error")) m_metrics["max_error"]->setText(QString::number(maxError, 'f', 2) + " mm");
    if (m_metrics.contains("track_error")) m_metrics["track_error"]->setText(QString::number(trackError, 'f', 2) + " mm");
    if (m_metrics.contains("settling")) m_metrics["settling"]->setText(settling);
}

void MetricsPanel::clear() {
    for (auto& label : m_metrics) {
        label->setText("--");
    }
}
