/**
 * MetricsPanel.h - 性能指标面板
 */

#ifndef METRICSPANEL_H
#define METRICSPANEL_H

#include <QGroupBox>
#include <QStackedWidget>
#include <QLabel>
#include <QMap>

struct PerformanceMetrics;

/**
 * @brief 统一性能指标面板
 */
class MetricsPanel : public QGroupBox {
    Q_OBJECT

public:
    // 模式常量
    static constexpr int ModeSerial = 0;
    static constexpr int ModePendulum = 1;
    static constexpr int ModeBall = 2;

    explicit MetricsPanel(QWidget* parent = nullptr);

    /**
     * @brief 设置显示模式
     */
    void setMode(int mode);

    /**
     * @brief 更新串口模式指标
     */
    void updateSerialMetrics(const PerformanceMetrics& metrics);

    /**
     * @brief 更新倒立摆指标
     */
    void updatePendulumMetrics(double angle, double cartPos, double force,
                               double maxAngle, double angularVel = 0.0,
                               const QString& settling = "--");

    /**
     * @brief 更新滚球系统指标
     */
    void updateBallMetrics(double error, double ballX, double ballY,
                           double plateX, double plateY, double maxError,
                           double trackError = 0.0, const QString& settling = "--");

    /**
     * @brief 清空所有指标
     */
    void clear();

private:
    void setupUi();
    QWidget* createMetricsGrid(const QVector<std::tuple<QString, QString, QString>>& config);

private:
    QStackedWidget* m_stack;
    QMap<QString, QLabel*> m_metrics;
    int m_currentMode = ModeSerial;
};

#endif // METRICSPANEL_H
