/**
 * SliderWithLabel.h - 带标签的滑块控件
 */

#ifndef SLIDERWITHLABEL_H
#define SLIDERWITHLABEL_H

#include <QWidget>
#include <QSlider>
#include <QDoubleSpinBox>
#include <QLabel>

/**
 * @brief 带标签的滑块控件
 */
class SliderWithLabel : public QWidget {
    Q_OBJECT

public:
    explicit SliderWithLabel(const QString& label,
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
    void onSliderChanged(int value);
    void onSpinboxChanged(double value);

private:
    void setupUi(const QString& label);

private:
    int m_decimals;
    double m_scale;

    QLabel* m_label;
    QSlider* m_slider;
    QDoubleSpinBox* m_spinbox;
};

#endif // SLIDERWITHLABEL_H
