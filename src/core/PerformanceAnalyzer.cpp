// PerformanceAnalyzer.cpp - 性能分析模块实现 (存根)
#include "core/PerformanceAnalyzer.h"
#include <cmath>
#include <numeric>

PerformanceAnalyzer::PerformanceAnalyzer() = default;

PerformanceMetrics PerformanceAnalyzer::analyze(const QVector<double>& timestamps, const QVector<double>& setpoints,
    const QVector<double>& processValues, const QVector<double>& errors) {
    PerformanceMetrics metrics;
    if (timestamps.isEmpty() || errors.isEmpty()) return metrics;

    // 计算基本统计量
    double sumError = 0, sumAbsError = 0, sumSqError = 0;
    double maxError = 0;
    for (int i = 0; i < errors.size(); ++i) {
        double e = errors[i];
        sumError += e;
        sumAbsError += std::abs(e);
        sumSqError += e * e;
        maxError = std::max(maxError, std::abs(e));
    }

    metrics.meanError = sumError / errors.size();
    metrics.rmsError = std::sqrt(sumSqError / errors.size());
    metrics.maxError = maxError;
    metrics.iae = sumAbsError;
    metrics.ise = sumSqError;

    analyzeStepResponse(timestamps, setpoints, processValues, metrics);
    metrics.oscillationCount = countOscillations(errors);

    return metrics;
}

void PerformanceAnalyzer::analyzeStepResponse(const QVector<double>& timestamps, const QVector<double>& setpoints,
    const QVector<double>& processValues, PerformanceMetrics& metrics) {
    if (timestamps.size() < 10) return;

    double sp = setpoints.isEmpty() ? 0 : setpoints.last();
    double initialValue = processValues.first();
    double finalChange = sp - initialValue;

    if (std::abs(finalChange) < 1e-6) return;

    double threshold10 = initialValue + 0.1 * finalChange;
    double threshold90 = initialValue + 0.9 * finalChange;

    double t10 = -1, t90 = -1;
    for (int i = 0; i < processValues.size(); ++i) {
        if (t10 < 0 && processValues[i] >= threshold10) t10 = timestamps[i];
        if (t90 < 0 && processValues[i] >= threshold90) t90 = timestamps[i];
    }

    if (t10 >= 0 && t90 >= 0 && t90 > t10) {
        metrics.riseTime = t90 - t10;
    }
}

int PerformanceAnalyzer::countOscillations(const QVector<double>& errors) {
    int count = 0;
    for (int i = 1; i < errors.size() - 1; ++i) {
        if ((errors[i] > errors[i-1] && errors[i] > errors[i+1]) ||
            (errors[i] < errors[i-1] && errors[i] < errors[i+1])) {
            count++;
        }
    }
    return count / 2;
}

std::pair<QVector<double>, QVector<double>> PerformanceAnalyzer::computeFFT(const QVector<double>& timestamps, const QVector<double>& signal) {
    return {QVector<double>(), QVector<double>()};
}

std::pair<QVector<double>, QVector<double>> PerformanceAnalyzer::computePSD(const QVector<double>& timestamps, const QVector<double>& signal) {
    return {QVector<double>(), QVector<double>()};
}
