// AnalysisWindow.cpp - 分析窗口实现 (存根)
#include "ui/windows/AnalysisWindow.h"
#include "ui/plots/RealtimePlotWidget.h"
#include "ui/plots/FFTPlotWidget.h"
#include <QVBoxLayout>

AnalysisWindow::AnalysisWindow(QWidget* parent) : QMainWindow(parent) { setupUi(); }
AnalysisWindow::~AnalysisWindow() = default;

void AnalysisWindow::setupUi() {
    setWindowTitle("详细分析");
    resize(800, 600);
    QWidget* central = new QWidget();
    setCentralWidget(central);
    QVBoxLayout* layout = new QVBoxLayout(central);
    m_errorPlot = new RealtimePlotWidget("误差曲线");
    m_errorPlot->addCurve("error", "#FFE66D", 2);
    layout->addWidget(m_errorPlot);
    m_outputPlot = new RealtimePlotWidget("控制输出");
    m_outputPlot->addCurve("output", "#95E1D3", 2);
    layout->addWidget(m_outputPlot);
    m_fftPlot = new FFTPlotWidget();
    layout->addWidget(m_fftPlot);
}

void AnalysisWindow::updateData(const QVector<double>& timestamps, const QVector<double>& setpoints,
    const QVector<double>& processValues, const QVector<double>& errors, const QVector<double>& outputs) {
    m_errorPlot->updateCurve("error", timestamps, errors);
    m_outputPlot->updateCurve("output", timestamps, outputs);
}

void AnalysisWindow::updateFFT(const QVector<double>& frequencies, const QVector<double>& magnitudes) {
    m_fftPlot->updateData(frequencies, magnitudes);
}

void AnalysisWindow::clearAll() { m_errorPlot->clearCurves(); m_outputPlot->clearCurves(); }
