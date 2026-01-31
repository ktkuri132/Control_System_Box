/**
 * DialWithLabel.h - 带标签的旋钮控件
 */

#ifndef DIALWITHLABEL_H
#define DIALWITHLABEL_H

#include <QWidget>
#include <QDial>
#include <QDoubleSpinBox>
#include <QLabel>

/**
 * @brief 带标签的旋钮控件
 */
class DialWithLabel : public QWidget {
    Q_OBJECT

public:
    explicit DialWithLabel(const QString& label,
                           double minVal, double maxVal,
                           double defaultVal = 0.0,
                           int decimals = 2,
                           QWidget* parent = nullptr);

    double value() const;
    void setValue(double value);

    void setRange(double min, double max);

signals:
    void valueChanged(double value);

private slots:
    void onDialChanged(int value);
    void onSpinboxChanged(double value);

private:
    void setupUi(const QString& label);

private:
    int m_decimals;
    double m_min;
    double m_max;
    double m_scale;

    QLabel* m_label;
    QDial* m_dial;
    QDoubleSpinBox* m_spinbox;
};

#endif // DIALWITHLABEL_H
