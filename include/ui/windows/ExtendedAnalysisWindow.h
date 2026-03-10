/**
 * ExtendedAnalysisWindow.h - 扩展分析窗口
 */

#ifndef EXTENDEDANALYSISWINDOW_H
#define EXTENDEDANALYSISWINDOW_H

#include <QMainWindow>
#include <QVector>

class MetricCard;
class StabilityGauge;
class QChart;
class QChartView;
class QLineSeries;

/**
 * @brief 扩展分析窗口 - 性能指标、稳定性评估、波特图
 */
class ExtendedAnalysisWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit ExtendedAnalysisWindow(QWidget* parent = nullptr);
    ~ExtendedAnalysisWindow() override;

    /**
     * @brief 更新数据并分析
     */
    void updateData(const QVector<double>& timestamps,
                    const QVector<double>& setpoints,
                    const QVector<double>& processValues,
                    const QVector<double>& errors,
                    const QVector<double>& outputs);

    /**
     * @brief 清空所有数据
     */
    void clearAll();

private slots:
    void refreshAnalysis();

private:
    void setupUi();
    void analyzePerformance();

    // 分析方法
    void calculateTimeDomainMetrics(const QVector<double>& timestamps,
                                    const QVector<double>& setpoints,
                                    const QVector<double>& processValues,
                                    const QVector<double>& errors);
    void calculateDynamicMetrics(const QVector<double>& timestamps,
                                 const QVector<double>& setpoints,
                                 const QVector<double>& processValues,
                                 const QVector<double>& errors);
    void calculateFrequencyDomainMetrics(const QVector<double>& timestamps,
                                         const QVector<double>& errors);
    void calculateStatisticalMetrics(const QVector<double>& timestamps,
                                     const QVector<double>& errors);
    void calculateControlEnergyMetrics(const QVector<double>& timestamps,
                                       const QVector<double>& outputs);
    void updateErrorHistogram(const QVector<double>& errors);
    void calculateStabilityScore(const QVector<double>& timestamps,
                                 const QVector<double>& setpoints,
                                 const QVector<double>& processValues,
                                 const QVector<double>& errors);

private:
    // 缓存数据
    QVector<double> m_timestamps;
    QVector<double> m_setpoints;
    QVector<double> m_processValues;
    QVector<double> m_errors;
    QVector<double> m_outputs;

    // 稳定性评估
    StabilityGauge* m_stabilityGauge;

    // 时域性能指标卡片
    MetricCard* m_riseTimeCard;
    MetricCard* m_settlingTimeCard;
    MetricCard* m_overshootCard;
    MetricCard* m_peakTimeCard;
    MetricCard* m_delayTimeCard;
    MetricCard* m_steadyErrorCard;

    // 动态特性指标卡片
    MetricCard* m_oscillationCard;
    MetricCard* m_dampingRatioCard;
    MetricCard* m_naturalFreqCard;
    MetricCard* m_decayRatioCard;

    // 频域性能指标卡片
    MetricCard* m_bandwidthCard;
    MetricCard* m_resonanceCard;
    MetricCard* m_resonanceFreqCard;
    MetricCard* m_cutoffFreqCard;
    MetricCard* m_phaseMarginCard;
    MetricCard* m_gainMarginCard;

    // 统计与质量指标卡片
    MetricCard* m_iaeCard;
    MetricCard* m_iseCard;
    MetricCard* m_itaeCard;
    MetricCard* m_rmseCard;
    MetricCard* m_maeCard;
    MetricCard* m_stdErrorCard;

    // 控制能量指标卡片
    MetricCard* m_controlEffortCard;
    MetricCard* m_maxControlCard;
    MetricCard* m_controlVarianceCard;
    MetricCard* m_smoothnessCard;

    // 图表
    QChartView* m_stepResponseView;
    QLineSeries* m_responseCurve;
    QLineSeries* m_setpointCurve;

    QChartView* m_bodeMagView;
    QLineSeries* m_bodeMagCurve;

    QChartView* m_errorHistView;
};

#endif // EXTENDEDANALYSISWINDOW_H
