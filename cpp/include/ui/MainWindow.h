/**
 * MainWindow.h - 主窗口头文件
 *
 * 统一架构版本 - 串口和仿真模式共用相同的核心组件
 */

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTimer>
#include <QStatusBar>
#include <QStackedWidget>
#include <QButtonGroup>
#include <QRadioButton>
#include <QLabel>
#include <memory>

// 前向声明
class SerialManager;
class SimulatorReceiver;
class PerformanceAnalyzer;
class DataProcessor;
class UnifiedControlPanel;
class SimulatorPlotWidget;

struct UnifiedData;
struct HandshakeInfo;

/**
 * @brief 数据源模式
 */
enum class DataSourceMode {
    Serial = 0,     ///< 串口模式
    Simulator = 1   ///< UDP仿真模式
};

/**
 * @brief 主窗口类
 *
 * 统一架构，串口和仿真共用相同的核心组件
 */
class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

protected:
    void closeEvent(QCloseEvent *event) override;

private slots:
    // 模式切换
    void onModeChanged(int modeId);

    // 串口连接
    void connectSerial(const QString& port, int baudrate);
    void disconnectSerial();
    void onSerialConnectionChanged(bool connected);

    // UDP仿真连接
    void connectSimulator(const QString& host, int port);
    void disconnectSimulator();
    void onSimulatorConnectionChanged(bool connected, const QString& message);

    // 数据处理
    void onHandshakeReceived(const HandshakeInfo& handshake);
    void onDataReceived(const UnifiedData& data);
    void onDataProcessed(const QVariantMap& result);
    void onError(const QString& message);

    // 控制命令
    void sendPIDParams(double kp, double ki, double kd);
    void sendSetpoint(double setpoint);

    // 数据管理
    void setPaused(bool paused);
    void clearData();
    void exportData();

    // 定时更新
    void updatePlots();
    void updateMetrics();
    void updateFFT();

    // 滤波设置
    void onFilterChanged();

    // 菜单操作
    void showAbout();
    void showProtocolHelp();
    void checkForUpdates();

private:
    void setupUi();
    void setupStyles();
    void setupModeToolbar(QVBoxLayout* parentLayout);
    void setupMenu();
    void setupConnections();
    void setupTimers();

private:
    // 当前模式
    DataSourceMode m_currentMode;

    // 核心组件
    std::unique_ptr<SerialManager> m_serialManager;
    std::unique_ptr<SimulatorReceiver> m_simulatorReceiver;
    std::unique_ptr<PerformanceAnalyzer> m_analyzer;
    std::unique_ptr<DataProcessor> m_dataProcessor;

    // 数据缓冲
    // HighPerformanceBuffer m_dataBuffer;  // 使用专门的高性能缓冲区类

    // UI组件
    UnifiedControlPanel* m_controlPanel;
    SimulatorPlotWidget* m_plotWidget;
    QStatusBar* m_statusBar;

    // 模式切换组件
    QButtonGroup* m_modeGroup;
    QRadioButton* m_serialModeBtn;
    QRadioButton* m_simulatorModeBtn;
    QLabel* m_modeIndicator;

    // 定时器
    QTimer* m_plotTimer;
    QTimer* m_metricsTimer;
    QTimer* m_fftTimer;

    // 状态
    bool m_isPaused;
    std::unique_ptr<HandshakeInfo> m_handshake;
};

#endif // MAINWINDOW_H
