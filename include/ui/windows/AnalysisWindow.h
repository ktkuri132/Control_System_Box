/**
 * AnalysisWindow.h - 详细分析窗口
 */

#ifndef ANALYSISWINDOW_H
#define ANALYSISWINDOW_H

#include <QMainWindow>
#include <QVector>

class RealtimePlotWidget;
class FFTPlotWidget;

/**
 * @brief 独立的详细分析窗口 - 误差/控制输出/FFT
 */
class AnalysisWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit AnalysisWindow(QWidget* parent = nullptr);
    ~AnalysisWindow() override;

    /**
     * @brief 更新数据
     */
    void updateData(const QVector<double>& timestamps,
                    const QVector<double>& setpoints,
                    const QVector<double>& processValues,
                    const QVector<double>& errors,
                    const QVector<double>& outputs);

    /**
     * @brief 更新FFT数据
     */
    void updateFFT(const QVector<double>& frequencies,
                   const QVector<double>& magnitudes);

    /**
     * @brief 清空所有数据
     */
    void clearAll();

private:
    void setupUi();

private:
    RealtimePlotWidget* m_errorPlot;
    RealtimePlotWidget* m_outputPlot;
    FFTPlotWidget* m_fftPlot;
};

#endif // ANALYSISWINDOW_H
