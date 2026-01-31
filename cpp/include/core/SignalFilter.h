/**
 * SignalFilter.h - 信号滤波模块
 */

#ifndef SIGNALFILTER_H
#define SIGNALFILTER_H

#include <QVector>
#include <QString>
#include <deque>
#include <memory>

/**
 * @brief 滤波器类型
 */
namespace FilterType {
    constexpr const char* None = "none";
    constexpr const char* MovingAverage = "moving_average";
    constexpr const char* Exponential = "exponential";
    constexpr const char* Lowpass = "lowpass";
    constexpr const char* Median = "median";
    constexpr const char* Kalman = "kalman";
    constexpr const char* Fusion = "fusion";
}

/**
 * @brief 一维卡尔曼滤波器
 */
class KalmanFilter1D {
public:
    KalmanFilter1D(double processVariance = 1e-5, double measurementVariance = 1e-2);

    double update(double measurement);
    void reset();

private:
    double m_processVariance;
    double m_measurementVariance;
    double m_estimate = 0.0;
    double m_estimateError = 1.0;
    bool m_initialized = false;
};

/**
 * @brief 信号滤波器
 */
class SignalFilter {
public:
    SignalFilter();

    // 属性访问
    bool isEnabled() const { return m_enabled; }
    void setEnabled(bool enabled);

    QString filterType() const { return m_filterType; }
    void setFilterType(const QString& type);

    int strength() const { return m_strength; }
    void setStrength(int strength);

    int windowSize() const { return m_strength * 2 + 1; }

    /**
     * @brief 获取滤波器类型的英文键名
     */
    QString getFilterTypeKey() const;

    /**
     * @brief 对单个值进行滤波
     */
    double filter(double value);

    /**
     * @brief 对数组进行滤波
     */
    QVector<double> filterArray(const QVector<double>& values);

    /**
     * @brief 重置滤波器状态
     */
    void reset();

private:
    double movingAverage(double value);
    double exponentialSmoothing(double value);
    double lowpassFilter(double value);
    double medianFilter(double value);
    double kalmanFilter(double value);
    double fusionFilter(double value);
    void updateLowpassCoeffs();

private:
    QString m_filterType;
    int m_strength = 5;
    bool m_enabled = false;

    std::deque<double> m_buffer;
    std::unique_ptr<KalmanFilter1D> m_kalman;
    double m_lastEma = 0.0;
    bool m_hasLastEma = false;

    // 低通滤波器系数
    QVector<double> m_lowpassB;
    QVector<double> m_lowpassA;
    double m_lowpassZi = 0.0;
};

/**
 * @brief 谐波分析器
 */
class HarmonicAnalyzer {
public:
    explicit HarmonicAnalyzer(double sampleRate = 100.0);

    void setSampleRate(double rate) { m_sampleRate = rate; }
    double sampleRate() const { return m_sampleRate; }

    /**
     * @brief 分析信号的谐波成分
     * @param signal 输入信号
     * @return 分析结果 (THD, 基频, 谐波列表)
     */
    struct AnalysisResult {
        double thd = 0.0;           ///< 总谐波失真
        double fundamentalFreq = 0.0; ///< 基频
        QVector<double> harmonicFreqs;  ///< 谐波频率
        QVector<double> harmonicMags;   ///< 谐波幅值
        QVector<double> harmonicPhases; ///< 谐波相位
    };

    AnalysisResult analyze(const QVector<double>& signal);

private:
    double m_sampleRate;
};

// 全局滤波器管理函数
SignalFilter& getFilter(int index);
void setAllFiltersEnabled(bool enabled);
void setAllFiltersType(const QString& type);
void setAllFiltersStrength(int strength);
void resetAllFilters();

#endif // SIGNALFILTER_H
