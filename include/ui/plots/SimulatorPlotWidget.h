/**
 * SimulatorPlotWidget.h - 仿真数据绘图组件（支持状态选择）
 */

#ifndef SIMULATORPLOTWIDGET_H
#define SIMULATORPLOTWIDGET_H

#include <QWidget>
#include <QComboBox>
#include <QLabel>
#include <QVector>
#include <QVariantMap>

#include "core/UnifiedDataProtocol.h"

class StandardResponseWidget;

/**
 * @brief 仿真数据绘图组件 - 支持状态选择
 */
class SimulatorPlotWidget : public QWidget {
    Q_OBJECT

public:
    explicit SimulatorPlotWidget(QWidget* parent = nullptr);
    ~SimulatorPlotWidget() override;

    /**
     * @brief 设置状态定义列表（从握手帧获取）
     */
    void setStateDefinitions(const QList<StateDefinition>& stateDefs);

    /**
     * @brief 获取当前选中的状态索引
     */
    int getSelectedStateIndex() const { return m_selectedStateIndex; }

    /**
     * @brief 设置系统类型
     */
    void setSystemType(const QString& systemType);

    /**
     * @brief 清空所有图表
     */
    void clearAll();

    /**
     * @brief 清空状态定义（断开连接时调用）
     */
    void clearStateDefinitions();

    /**
     * @brief 获取标准响应曲线组件
     */
    StandardResponseWidget* standardPlot() const { return m_standardPlot; }

signals:
    void stateSelectionChanged(int index);

private slots:
    void onStateSelected(int index);

private:
    void setupUi();

private:
    QString m_currentSystem;
    QList<StateDefinition> m_stateDefs;
    int m_selectedStateIndex = 0;

    QComboBox* m_stateCombo;
    QLabel* m_stateInfoLabel;
    QLabel* m_systemLabel;

    StandardResponseWidget* m_standardPlot;
};

/**
 * @brief 标准响应控制曲线组件
 */
class StandardResponseWidget : public QWidget {
    Q_OBJECT

public:
    explicit StandardResponseWidget(QWidget* parent = nullptr);
    ~StandardResponseWidget() override;

    /**
     * @brief 更新数据
     */
    void updateData(const QVector<double>& timestamps,
                    const QVector<double>& setpoints,
                    const QVector<double>& processValues,
                    const QVector<double>& errors,
                    const QVector<double>& outputs,
                    const QVector<double>& rawValues = QVector<double>());

    /**
     * @brief 更新FFT数据
     */
    void updateFFT(const QVector<double>& frequencies,
                   const QVector<double>& magnitudes);

    /**
     * @brief 设置是否显示原始值曲线
     */
    void setShowRaw(bool show);

    /**
     * @brief 清空所有图表
     */
    void clearAll();

private slots:
    void openAnalysisWindow();
    void openExtendedWindow();

private:
    void setupUi();

private:
    class RealtimePlotWidget* m_responsePlot;
    class AnalysisWindow* m_analysisWindow = nullptr;
    class ExtendedAnalysisWindow* m_extendedWindow = nullptr;

    QVariantMap m_cachedData;
    bool m_showRaw = false;
};

#endif // SIMULATORPLOTWIDGET_H
