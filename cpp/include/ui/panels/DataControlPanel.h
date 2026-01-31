/**
 * DataControlPanel.h - 数据控制面板
 */

#ifndef DATACONTROLPANEL_H
#define DATACONTROLPANEL_H

#include <QGroupBox>
#include <QPushButton>
#include <QLabel>

/**
 * @brief 数据控制面板
 */
class DataControlPanel : public QGroupBox {
    Q_OBJECT

public:
    explicit DataControlPanel(QWidget* parent = nullptr);

    /**
     * @brief 设置数据点数
     */
    void setDataCount(int count);

signals:
    void clearRequested();
    void pauseRequested(bool paused);
    void exportRequested();

private slots:
    void onPauseClicked();
    void onClearClicked();

private:
    void setupUi();

private:
    QLabel* m_countLabel;
    QPushButton* m_pauseBtn;
    QPushButton* m_clearBtn;
    QPushButton* m_exportBtn;

    bool m_isPaused = false;
};

#endif // DATACONTROLPANEL_H
