/**
 * UnifiedControlPanel.h - 统一控制面板
 */

#ifndef UNIFIEDCONTROLPANEL_H
#define UNIFIEDCONTROLPANEL_H

#include <QWidget>
#include <QStackedWidget>

// 前向声明
class SerialConfigPanel;
class SimulatorConfigPanel;
class SetpointPanel;
class PIDControlPanel;
class MetricsPanel;
class DataControlPanel;
class FilterPanel;

/**
 * @brief 统一控制面板
 *
 * 将两种模式的控制面板合并，共用相同组件
 */
class UnifiedControlPanel : public QWidget {
    Q_OBJECT

public:
    explicit UnifiedControlPanel(QWidget* parent = nullptr);
    ~UnifiedControlPanel() override;

    /**
     * @brief 设置当前模式
     * @param mode 0=串口, 1=仿真
     */
    void setMode(int mode);

    // 子面板访问
    SerialConfigPanel* serialPanel() const { return m_serialPanel; }
    SimulatorConfigPanel* simulatorPanel() const { return m_simulatorPanel; }
    SetpointPanel* setpointPanel() const { return m_setpointPanel; }
    PIDControlPanel* pidPanel() const { return m_pidPanel; }
    MetricsPanel* metricsPanel() const { return m_metricsPanel; }
    DataControlPanel* dataPanel() const { return m_dataPanel; }
    FilterPanel* filterPanel() const { return m_filterPanel; }

private:
    void setupUi();

private:
    QStackedWidget* m_connectionStack;

    SerialConfigPanel* m_serialPanel;
    SimulatorConfigPanel* m_simulatorPanel;
    SetpointPanel* m_setpointPanel;
    PIDControlPanel* m_pidPanel;
    MetricsPanel* m_metricsPanel;
    DataControlPanel* m_dataPanel;
    FilterPanel* m_filterPanel;
};

#endif // UNIFIEDCONTROLPANEL_H
