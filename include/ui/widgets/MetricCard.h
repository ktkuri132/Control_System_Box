/**
 * MetricCard.h - 性能指标卡片
 */

#ifndef METRICCARD_H
#define METRICCARD_H

#include <QFrame>
#include <QLabel>

/**
 * @brief 性能指标卡片
 */
class MetricCard : public QFrame {
    Q_OBJECT

public:
    explicit MetricCard(const QString& title,
                        const QString& unit = "",
                        QWidget* parent = nullptr);

    /**
     * @brief 设置数值
     * @param value 数值
     * @param statusColor 状态颜色 (可选)
     * @param statusText 状态文字 (可选)
     */
    void setValue(double value,
                  const QString& statusColor = "",
                  const QString& statusText = "");

    void setValue(const QString& text,
                  const QString& statusColor = "");

    /**
     * @brief 清空数值
     */
    void clear();

private:
    void setupUi(const QString& title, const QString& unit);

private:
    QString m_unit;
    QLabel* m_titleLabel;
    QLabel* m_valueLabel;
    QLabel* m_statusLabel;
};

#endif // METRICCARD_H
