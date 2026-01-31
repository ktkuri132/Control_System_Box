/**
 * SerialConfigPanel.h - 串口配置面板
 */

#ifndef SERIALCONFIGPANEL_H
#define SERIALCONFIGPANEL_H

#include <QGroupBox>
#include <QComboBox>
#include <QPushButton>
#include <QLabel>

/**
 * @brief 串口配置面板
 */
class SerialConfigPanel : public QGroupBox {
    Q_OBJECT

public:
    explicit SerialConfigPanel(QWidget* parent = nullptr);

    /**
     * @brief 刷新串口列表
     */
    void refreshPorts();

    /**
     * @brief 设置连接状态
     */
    void setConnected(bool connected);

signals:
    void connectRequested(const QString& port, int baudrate);
    void disconnectRequested();

private slots:
    void onConnectClicked();

private:
    void setupUi();
    void applyStyles();

private:
    QComboBox* m_portCombo;
    QPushButton* m_refreshBtn;
    QComboBox* m_baudrateCombo;
    QPushButton* m_connectBtn;
    QLabel* m_statusLabel;

    bool m_isConnected = false;
};

#endif // SERIALCONFIGPANEL_H
