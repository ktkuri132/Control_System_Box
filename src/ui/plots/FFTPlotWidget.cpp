// FFTPlotWidget.cpp
#include "ui/plots/FFTPlotWidget.h"

FFTPlotWidget::FFTPlotWidget(QWidget* parent) : RealtimePlotWidget("FFT 频谱分析", parent) {
    setYLabel("幅值", "dB");
    addCurve("magnitude", "#FF6B6B", 1);
}

void FFTPlotWidget::updateData(const QVector<double>& frequencies, const QVector<double>& magnitudes) {
    updateCurve("magnitude", frequencies, magnitudes);
}
