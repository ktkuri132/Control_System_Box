/**
 * FilterPanel.h - 滤波控制面板
 */

#ifndef FILTERPANEL_H
#define FILTERPANEL_H

#include <QWidget>
#include <QGroupBox>
#include <QCheckBox>
#include <QComboBox>
#include <QSlider>
#include <QLabel>
#include <QTableWidget>

/**
 * @brief 滤波控制面板
 */
class FilterPanel : public QWidget {
    Q_OBJECT

public:
    explicit FilterPanel(QWidget* parent = nullptr);

    /**
     * @brief 更新谐波分析结果
     */
    struct HarmonicAnalysis {
        double thd = 0.0;
        double fundamentalFreq = 0.0;
        QVector<double> harmonicFreqs;
        QVector<double> harmonicMags;
        QVector<double> harmonicPhases;
    };

    void updateHarmonicAnalysis(const HarmonicAnalysis& analysis);

signals:
    void filterChanged();

private slots:
    void onEnableChanged(int state);
    void onAlgoChanged(const QString& text);
    void onStrengthChanged(int value);

private:
    void setupUi();
    void updateAlgoDescription();
    void setControlsEnabled(bool enabled);

private:
    // 滤波设置
    QGroupBox* m_filterGroup;
    QCheckBox* m_enableCheck;
    QComboBox* m_algoCombo;
    QSlider* m_strengthSlider;
    QLabel* m_strengthValue;
    QLabel* m_algoDesc;

    // 谐波分析
    QGroupBox* m_harmonicGroup;
    QLabel* m_thdValue;
    QLabel* m_fundValue;
    QTableWidget* m_harmonicTable;
};

#endif // FILTERPANEL_H
