/**
 * RealtimePlotWidget.h - 实时绑图组件
 */

#ifndef REALTIMEPLOTWIDGET_H
#define REALTIMEPLOTWIDGET_H

#include <QWidget>
#include <QVector>
#include <QMap>
#include <QPushButton>
#include <QComboBox>
#include <QLabel>

// 使用 Qt Charts
#include <QtCharts/QChartView>
#include <QtCharts/QLineSeries>
#include <QtCharts/QValueAxis>

/**
 * @brief 实时绑图组件
 */
class RealtimePlotWidget : public QWidget {
    Q_OBJECT

public:
    // 预定义颜色
    static const QMap<QString, QString> Colors;

    explicit RealtimePlotWidget(const QString& title = "实时曲线",
                                QWidget* parent = nullptr);
    ~RealtimePlotWidget() override;

    /**
     * @brief 添加曲线
     * @param name 曲线名称
     * @param color 颜色
     * @param width 线宽
     */
    void addCurve(const QString& name,
                  const QString& color = "",
                  int width = 2);

    /**
     * @brief 更新曲线数据
     */
    void updateCurve(const QString& name,
                     const QVector<double>& x,
                     const QVector<double>& y);

    /**
     * @brief 清空所有曲线数据
     */
    void clearCurves();

    /**
     * @brief 设置Y轴标签
     */
    void setYLabel(const QString& label, const QString& units = "");

    /**
     * @brief 设置X轴范围
     */
    void setXRange(double min, double max);

    /**
     * @brief 设置Y轴范围
     */
    void setYRange(double min, double max);

    /**
     * @brief 启用/禁用自动缩放
     */
    void enableAutoRange(bool enable = true);

    /**
     * @brief 设置最大显示点数
     */
    void setMaxPoints(int points) { m_maxPoints = points; }

signals:
    void autoScaleToggled(bool enabled);

private slots:
    void onAutoScaleClicked(bool checked);
    void onPointsChanged(const QString& text);

private:
    void setupUi();
    void updateValueDisplay();

private:
    QString m_title;
    int m_maxPoints = 1000;
    bool m_autoScale = true;

    // Qt Charts 组件
    QChart* m_chart;
    QChartView* m_chartView;
    QValueAxis* m_axisX;
    QValueAxis* m_axisY;
    QMap<QString, QLineSeries*> m_curves;
    QMap<QString, double> m_latestValues;

    // UI 组件
    QLabel* m_titleLabel;
    QLabel* m_valueLabel;
    QPushButton* m_autoScaleBtn;
    QComboBox* m_pointsCombo;
};

#endif // REALTIMEPLOTWIDGET_H
