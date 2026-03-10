/**
 * PerformanceAnalyzer.h - 性能分析模块
 */

#ifndef PERFORMANCEANALYZER_H
#define PERFORMANCEANALYZER_H

#include <QVector>
#include <optional>

/**
 * @brief 控制系统性能指标
 */
struct PerformanceMetrics {
    // 时域指标
    std::optional<double> riseTime;         ///< 上升时间 (秒)
    std::optional<double> settlingTime;     ///< 调节时间 (秒)
    std::optional<double> overshoot;        ///< 超调量 (%)
    std::optional<double> peakTime;         ///< 峰值时间 (秒)
    std::optional<double> peakValue;        ///< 峰值
    std::optional<double> steadyStateError; ///< 稳态误差
    int oscillationCount = 0;               ///< 振荡次数

    // 统计指标
    std::optional<double> meanError;        ///< 平均误差
    std::optional<double> rmsError;         ///< 均方根误差
    std::optional<double> maxError;         ///< 最大误差
    std::optional<double> iae;              ///< 积分绝对误差
    std::optional<double> ise;              ///< 积分平方误差
    std::optional<double> itae;             ///< 时间加权积分绝对误差
};

/**
 * @brief 性能分析器
 */
class PerformanceAnalyzer {
public:
    PerformanceAnalyzer();

    /**
     * @brief 设置稳态阈值
     */
    void setSettlingThreshold(double threshold) { m_settlingThreshold = threshold; }

    /**
     * @brief 设置上升时间阈值 (起始, 结束)
     */
    void setRiseThreshold(double start, double end) {
        m_riseThresholdStart = start;
        m_riseThresholdEnd = end;
    }

    /**
     * @brief 分析系统性能
     * @param timestamps 时间戳数组
     * @param setpoints 设定值数组
     * @param processValues 过程值数组
     * @param errors 误差数组
     * @return 性能指标
     */
    PerformanceMetrics analyze(const QVector<double>& timestamps,
                               const QVector<double>& setpoints,
                               const QVector<double>& processValues,
                               const QVector<double>& errors);

    /**
     * @brief 计算 FFT
     * @param timestamps 时间戳数组
     * @param signal 信号数组
     * @return (频率, 幅值) 数组对
     */
    std::pair<QVector<double>, QVector<double>>
    computeFFT(const QVector<double>& timestamps, const QVector<double>& signal);

    /**
     * @brief 计算功率谱密度 (PSD)
     */
    std::pair<QVector<double>, QVector<double>>
    computePSD(const QVector<double>& timestamps, const QVector<double>& signal);

private:
    void analyzeStepResponse(const QVector<double>& timestamps,
                            const QVector<double>& setpoints,
                            const QVector<double>& processValues,
                            PerformanceMetrics& metrics);

    int countOscillations(const QVector<double>& errors);

private:
    double m_settlingThreshold = 0.02;  ///< 2% 稳态误差阈值
    double m_riseThresholdStart = 0.1;  ///< 上升时间起始: 10%
    double m_riseThresholdEnd = 0.9;    ///< 上升时间结束: 90%
};

#endif // PERFORMANCEANALYZER_H
