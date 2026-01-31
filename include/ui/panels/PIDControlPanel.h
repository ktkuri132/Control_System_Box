/**
 * PIDControlPanel.h - PID参数控制面板
 */

#ifndef PIDCONTROLPANEL_H
#define PIDCONTROLPANEL_H

#include <QGroupBox>
#include <QCheckBox>
#include <QPushButton>
#include <QLabel>

class DialWithLabel;

/**
 * @brief PID参数控制面板
 */
class PIDControlPanel : public QGroupBox {
    Q_OBJECT

public:
    explicit PIDControlPanel(QWidget* parent = nullptr);

    /**
     * @brief 获取当前PID参数
     */
    void getValues(double& kp, double& ki, double& kd) const;

    /**
     * @brief 设置PID参数
     */
    void setValues(double kp, double ki, double kd);

signals:
    void pidChanged(double kp, double ki, double kd);
    void sendRequested(double kp, double ki, double kd);

private slots:
    void onValueChanged();
    void onRealtimeToggled(bool checked);
    void onSendClicked();

private:
    void setupUi();
    void applyStyles();

private:
    DialWithLabel* m_kpDial;
    DialWithLabel* m_kiDial;
    DialWithLabel* m_kdDial;
    QCheckBox* m_realtimeCheck;
    QPushButton* m_sendBtn;
    QLabel* m_paramsLabel;

    bool m_realtimeSend = false;
};

#endif // PIDCONTROLPANEL_H
