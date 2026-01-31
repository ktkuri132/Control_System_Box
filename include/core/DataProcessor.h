/**
 * DataProcessor.h - 多线程数据处理器
 */

#ifndef DATAPROCESSOR_H
#define DATAPROCESSOR_H

#include <QObject>
#include <QThread>
#include <QVector>
#include <QVariantMap>
#include <QMutex>
#include <functional>
#include <memory>
#include <queue>
#include <atomic>

/**
 * @brief 数据处理任务
 */
struct ProcessTask {
    QVector<double> timestamps;
    QVector<QVariantMap> states;
    int selectedIndex;
    QString filterType;
    double filterStrength;
    int windowSize;
    int downsampleTarget;
};

/**
 * @brief 数据处理结果
 */
struct ProcessResult {
    QVector<double> timestamps;
    QVector<double> setpoints;
    QVector<double> processValues;
    QVector<double> rawValues;
    QVector<double> errors;
    QVector<double> outputs;
};

/**
 * @brief 数据处理工作线程
 */
class DataProcessorWorker : public QThread {
    Q_OBJECT

public:
    explicit DataProcessorWorker(QObject* parent = nullptr);
    ~DataProcessorWorker() override;

    void stop();
    void submitTask(const ProcessTask& task);

signals:
    void resultReady(const QVariantMap& result);

protected:
    void run() override;

private:
    ProcessResult processTask(const ProcessTask& task);
    QVector<double> applyFilter(const QVector<double>& values,
                                const QString& filterType,
                                double strength,
                                int windowSize);
    std::pair<QVector<double>, QVector<double>>
    downsampleLTTB(const QVector<double>& x, const QVector<double>& y, int targetPoints);

private:
    std::atomic<bool> m_running{false};
    QMutex m_queueMutex;
    std::queue<ProcessTask> m_taskQueue;
};

/**
 * @brief 多线程数据处理器
 *
 * 使用 Qt Concurrent 或独立工作线程处理数据
 */
class DataProcessor : public QObject {
    Q_OBJECT

public:
    explicit DataProcessor(QObject* parent = nullptr);
    ~DataProcessor() override;

    /**
     * @brief 启动处理器
     */
    void start();

    /**
     * @brief 停止处理器
     */
    void stop();

    /**
     * @brief 设置滤波参数
     */
    void setFilter(const QString& type, double strength, int windowSize);

    /**
     * @brief 设置降采样目标点数
     */
    void setDownsampleTarget(int points) { m_downsampleTarget = points; }

    /**
     * @brief 提交处理任务
     */
    void submitTask(const QVector<double>& timestamps,
                    const QVector<QVariantMap>& states,
                    int selectedIndex);

signals:
    void dataProcessed(const QVariantMap& result);

private slots:
    void onResultReady(const QVariantMap& result);

private:
    std::unique_ptr<DataProcessorWorker> m_worker;

    QString m_filterType = "none";
    double m_filterStrength = 0.3;
    int m_windowSize = 5;
    int m_downsampleTarget = 500;
};

/**
 * @brief 图表更新节流器
 */
class PlotUpdateThrottler {
public:
    explicit PlotUpdateThrottler(int minIntervalMs = 50);

    /**
     * @brief 检查是否应该更新
     */
    bool shouldUpdate();

    /**
     * @brief 设置最小间隔
     */
    void setMinInterval(int ms) { m_minIntervalMs = ms; }

private:
    int m_minIntervalMs;
    qint64 m_lastUpdateTime = 0;
};

/**
 * @brief 数据降采样器
 */
class DataDownsampler {
public:
    /**
     * @brief LTTB 降采样算法
     * @param x X轴数据
     * @param y Y轴数据
     * @param targetPoints 目标点数
     * @return 降采样后的 (x, y)
     */
    static std::pair<QVector<double>, QVector<double>>
    lttb(const QVector<double>& x, const QVector<double>& y, int targetPoints);

    /**
     * @brief 简单降采样 (取间隔)
     */
    static std::pair<QVector<double>, QVector<double>>
    simple(const QVector<double>& x, const QVector<double>& y, int targetPoints);

    /**
     * @brief 峰值保留降采样
     */
    static std::pair<QVector<double>, QVector<double>>
    peakPreserving(const QVector<double>& x, const QVector<double>& y, int targetPoints);
};

#endif // DATAPROCESSOR_H
