/**
 * DataBuffer.cpp - 数据缓冲区实现
 */

#include "core/DataBuffer.h"

// ============ HighPerformanceBuffer 实现 ============

HighPerformanceBuffer::HighPerformanceBuffer(size_t maxSize)
    : m_maxSize(maxSize)
{
}

void HighPerformanceBuffer::append(double timestamp,
    const std::unordered_map<int, std::pair<double, double>>& states) {

    QWriteLocker locker(&m_lock);

    m_timestamps.push_back(timestamp);
    m_states.push_back(states);

    // 保持缓冲区大小
    while (m_timestamps.size() > m_maxSize) {
        m_timestamps.pop_front();
        m_states.pop_front();
    }
}

std::pair<QVector<double>, QVector<std::unordered_map<int, std::pair<double, double>>>>
HighPerformanceBuffer::getData(size_t n) const {

    QReadLocker locker(&m_lock);

    size_t count = (n == 0 || n > m_timestamps.size()) ? m_timestamps.size() : n;
    size_t start = m_timestamps.size() - count;

    QVector<double> timestamps;
    QVector<std::unordered_map<int, std::pair<double, double>>> states;

    timestamps.reserve(count);
    states.reserve(count);

    for (size_t i = start; i < m_timestamps.size(); ++i) {
        timestamps.append(m_timestamps[i]);
        states.append(m_states[i]);
    }

    return {timestamps, states};
}

void HighPerformanceBuffer::clear() {
    QWriteLocker locker(&m_lock);
    m_timestamps.clear();
    m_states.clear();
}

size_t HighPerformanceBuffer::size() const {
    QReadLocker locker(&m_lock);
    return m_timestamps.size();
}

// ============ DataBuffer 实现 ============

DataBuffer::DataBuffer(size_t maxSize)
    : m_maxSize(maxSize)
{
}

void DataBuffer::append(double timestamp, double sp, double pv, double out, double error) {
    QMutexLocker locker(&m_mutex);

    m_timestamps.push_back(timestamp);
    m_setpoints.push_back(sp);
    m_processValues.push_back(pv);
    m_outputs.push_back(out);
    m_errors.push_back(error);

    while (m_timestamps.size() > m_maxSize) {
        m_timestamps.pop_front();
        m_setpoints.pop_front();
        m_processValues.pop_front();
        m_outputs.pop_front();
        m_errors.pop_front();
    }
}

void DataBuffer::clear() {
    QMutexLocker locker(&m_mutex);
    m_timestamps.clear();
    m_setpoints.clear();
    m_processValues.clear();
    m_outputs.clear();
    m_errors.clear();
}

void DataBuffer::getArrays(QVector<double>& timestamps,
                           QVector<double>& setpoints,
                           QVector<double>& processValues,
                           QVector<double>& outputs,
                           QVector<double>& errors) const {
    QMutexLocker locker(&m_mutex);

    timestamps = QVector<double>(m_timestamps.begin(), m_timestamps.end());
    setpoints = QVector<double>(m_setpoints.begin(), m_setpoints.end());
    processValues = QVector<double>(m_processValues.begin(), m_processValues.end());
    outputs = QVector<double>(m_outputs.begin(), m_outputs.end());
    errors = QVector<double>(m_errors.begin(), m_errors.end());
}

void DataBuffer::getLatest(size_t n,
                           QVector<double>& timestamps,
                           QVector<double>& setpoints,
                           QVector<double>& processValues,
                           QVector<double>& outputs,
                           QVector<double>& errors) const {
    QMutexLocker locker(&m_mutex);

    size_t count = std::min(n, m_timestamps.size());
    size_t start = m_timestamps.size() - count;

    timestamps.clear();
    setpoints.clear();
    processValues.clear();
    outputs.clear();
    errors.clear();

    timestamps.reserve(count);
    setpoints.reserve(count);
    processValues.reserve(count);
    outputs.reserve(count);
    errors.reserve(count);

    auto it_t = m_timestamps.begin();
    auto it_sp = m_setpoints.begin();
    auto it_pv = m_processValues.begin();
    auto it_out = m_outputs.begin();
    auto it_err = m_errors.begin();

    std::advance(it_t, start);
    std::advance(it_sp, start);
    std::advance(it_pv, start);
    std::advance(it_out, start);
    std::advance(it_err, start);

    for (size_t i = 0; i < count; ++i) {
        timestamps.append(*it_t++);
        setpoints.append(*it_sp++);
        processValues.append(*it_pv++);
        outputs.append(*it_out++);
        errors.append(*it_err++);
    }
}
