/**
 * SetpointPanel.h - 设定值控制面板
 */

#ifndef SETPOINTPANEL_H
#define SETPOINTPANEL_H

#include <QGroupBox>
#include <QPushButton>

class SliderWithLabel;

/**
 * @brief 设定值控制面板
 */
class SetpointPanel : public QGroupBox {
    Q_OBJECT

public:
    explicit SetpointPanel(QWidget* parent = nullptr);

    double getValue() const;
    void setValue(double value);

signals:
    void setpointChanged(double value);
    void sendRequested(double value);

private slots:
    void onValueChanged(double value);
    void onSendClicked();

private:
    void setupUi();

private:
    SliderWithLabel* m_spSlider;
    QPushButton* m_sendBtn;
};

#endif // SETPOINTPANEL_H
