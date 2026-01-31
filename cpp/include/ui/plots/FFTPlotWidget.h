/**
 * FFTPlotWidget.h - FFT频谱图组件
 */

#ifndef FFTPLOTWIDGET_H
#define FFTPLOTWIDGET_H

#include "ui/plots/RealtimePlotWidget.h"

/**
 * @brief FFT频谱分析图
 */
class FFTPlotWidget : public RealtimePlotWidget {
    Q_OBJECT

public:
    explicit FFTPlotWidget(QWidget* parent = nullptr);

    /**
     * @brief 更新FFT数据
     */
    void updateData(const QVector<double>& frequencies,
                    const QVector<double>& magnitudes);
};

#endif // FFTPLOTWIDGET_H
