/**
 * StabilityGauge.h - 稳定性评估仪表盘
 */

#ifndef STABILITYGAUGE_H
#define STABILITYGAUGE_H

#include <QWidget>
#include <QLabel>
#include <QProgressBar>

/**
 * @brief 稳定性评估仪表盘
 */
class StabilityGauge : public QWidget {
    Q_OBJECT

public:
    explicit StabilityGauge(QWidget* parent = nullptr);

    /**
     * @brief 设置稳定性评分
     * @param score 评分 (0-100)
     * @param status 状态文字
     */
    void setScore(double score, const QString& status);

    /**
     * @brief 清空
     */
    void clear();

private:
    void setupUi();
    void updateColors(double score);

private:
    QLabel* m_titleLabel;
    QLabel* m_scoreLabel;
    QProgressBar* m_progressBar;
    QLabel* m_statusLabel;
};

#endif // STABILITYGAUGE_H
