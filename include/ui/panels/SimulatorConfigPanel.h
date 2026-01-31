/**
 * SimulatorConfigPanel.h - 仿真配置面板
 */

#ifndef SIMULATORCONFIGPANEL_H
#define SIMULATORCONFIGPANEL_H

#include <QGroupBox>
#include <QLineEdit>
#include <QSpinBox>
#include <QPushButton>
#include <QLabel>

/**
 * @brief UDP仿真配置面板
 */
class SimulatorConfigPanel : public QGroupBox {
    Q_OBJECT

public:
    explicit SimulatorConfigPanel(QWidget* parent = nullptr);

    /**
     * @brief 设置连接状态
     */
    void setConnected(bool connected, const QString& message = "");

    /**
     * @brief 设置系统类型信息
     */
    void setSystemType(const QString& systemType,
                       const QString& version = "2.0",
                       int stateCount = 0);

signals:
    void connectRequested(const QString& host, int port);
    void disconnectRequested();

private slots:
    void onConnectClicked();

private:
    void setupUi();
    void applyStyles();

private:
    QLineEdit* m_hostEdit;
    QSpinBox* m_portSpin;
    QPushButton* m_connectBtn;
    QLabel* m_statusLabel;
    QLabel* m_systemLabel;

    bool m_isConnected = false;
};

#endif // SIMULATORCONFIGPANEL_H
