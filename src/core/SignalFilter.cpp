// SignalFilter.cpp - 信号滤波模块实现 (存根)
#include "core/SignalFilter.h"
#include <QHash>

KalmanFilter1D::KalmanFilter1D(double processVariance, double measurementVariance)
    : m_processVariance(processVariance), m_measurementVariance(measurementVariance) {}

double KalmanFilter1D::update(double measurement) {
    if (!m_initialized) { m_estimate = measurement; m_initialized = true; return m_estimate; }
    double prediction = m_estimate;
    double predictionError = m_estimateError + m_processVariance;
    double gain = predictionError / (predictionError + m_measurementVariance);
    m_estimate = prediction + gain * (measurement - prediction);
    m_estimateError = (1 - gain) * predictionError;
    return m_estimate;
}

void KalmanFilter1D::reset() { m_initialized = false; m_estimate = 0; m_estimateError = 1; }

SignalFilter::SignalFilter() : m_filterType("none"), m_kalman(std::make_shared<KalmanFilter1D>()) {}
void SignalFilter::setEnabled(bool enabled) { m_enabled = enabled; }
void SignalFilter::setFilterType(const QString& type) { m_filterType = type; }
void SignalFilter::setStrength(int strength) { m_strength = strength; }
QString SignalFilter::getFilterTypeKey() const { return m_filterType; }
double SignalFilter::filter(double value) { if (!m_enabled) return value; return value; }
QVector<double> SignalFilter::filterArray(const QVector<double>& values) { if (!m_enabled) return values; return values; }
void SignalFilter::reset() { m_buffer.clear(); m_kalman->reset(); m_hasLastEma = false; }
double SignalFilter::movingAverage(double value) { return value; }
double SignalFilter::exponentialSmoothing(double value) { return value; }
double SignalFilter::lowpassFilter(double value) { return value; }
double SignalFilter::medianFilter(double value) { return value; }
double SignalFilter::kalmanFilter(double value) { return m_kalman->update(value); }
double SignalFilter::fusionFilter(double value) { return value; }
void SignalFilter::updateLowpassCoeffs() {}

HarmonicAnalyzer::HarmonicAnalyzer(double sampleRate) : m_sampleRate(sampleRate) {}
HarmonicAnalyzer::AnalysisResult HarmonicAnalyzer::analyze(const QVector<double>& signal) { return AnalysisResult(); }

// 全局滤波器管理 - 使用指针的QHash
static QHash<int, SignalFilter*> s_filters;

SignalFilter& getFilter(int index) {
    if (!s_filters.contains(index)) {
        s_filters.insert(index, new SignalFilter());
    }
    return *s_filters[index];
}

void setAllFiltersEnabled(bool enabled) {
    for (SignalFilter* f : s_filters) {
        if (f) f->setEnabled(enabled);
    }
}

void setAllFiltersType(const QString& type) {
    for (SignalFilter* f : s_filters) {
        if (f) f->setFilterType(type);
    }
}

void setAllFiltersStrength(int strength) {
    for (SignalFilter* f : s_filters) {
        if (f) f->setStrength(strength);
    }
}

void resetAllFilters() {
    for (SignalFilter* f : s_filters) {
        if (f) f->reset();
    }
}
