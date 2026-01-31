/**
 * DataBuffer.h - 高性能数据缓冲区
 */

#ifndef DATABUFFER_H
#define DATABUFFER_H

#include <QVector>
#include <QMutex>
#include <QReadWriteLock>
#include <deque>
#include <unordered_map>

/**
 * @brief 高性能环形数据缓冲区
 *
 * 使用 deque 实现环形缓冲，支持高效的头尾操作
 * 线程安全
 */
class HighPerformanceBuffer {
public:
    explicit HighPerformanceBuffer(size_t maxSize = 50000);

    /**
     * @brief 添加数据点
     * @param timestamp 时间戳
     * @param states 状态数据 {索引: {target, current}}
     */
    void append(double timestamp, const std::unordered_map<int, std::pair<double, double>>& states);

    /**
     * @brief 获取最近 n 个数据点
     * @param n 数据点数，0 表示全部
     * @return (时间戳数组, 状态数组)
     */
    std::pair<QVector<double>, QVector<std::unordered_map<int, std::pair<double, double>>>>
    getData(size_t n = 0) const;

    /**
     * @brief 清空缓冲区
     */
    void clear();

    /**
     * @brief 获取数据点数
     */
    size_t size() const;

    /**
     * @brief 是否为空
     */
    bool isEmpty() const { return size() == 0; }

private:
    size_t m_maxSize;
    mutable QReadWriteLock m_lock;

    std::deque<double> m_timestamps;
    std::deque<std::unordered_map<int, std::pair<double, double>>> m_states;
};

/**
 * @brief 简单数据缓冲区 (兼容旧接口)
 */
class DataBuffer {
public:
    explicit DataBuffer(size_t maxSize = 10000);

    void append(double timestamp, double sp, double pv, double out, double error);
    void clear();

    /**
     * @brief 获取 numpy 风格的数组数据
     */
    void getArrays(QVector<double>& timestamps,
                   QVector<double>& setpoints,
                   QVector<double>& processValues,
                   QVector<double>& outputs,
                   QVector<double>& errors) const;

    /**
     * @brief 获取最近 n 个数据点
     */
    void getLatest(size_t n,
                   QVector<double>& timestamps,
                   QVector<double>& setpoints,
                   QVector<double>& processValues,
                   QVector<double>& outputs,
                   QVector<double>& errors) const;

    size_t size() const { return m_timestamps.size(); }

private:
    size_t m_maxSize;
    mutable QMutex m_mutex;

    std::deque<double> m_timestamps;
    std::deque<double> m_setpoints;
    std::deque<double> m_processValues;
    std::deque<double> m_outputs;
    std::deque<double> m_errors;
};

#endif // DATABUFFER_H
