/**
 * DataControlPanel.cpp - 数据控制面板实现
 */

#include "ui/panels/DataControlPanel.h"

#include <QVBoxLayout>
#include <QHBoxLayout>

DataControlPanel::DataControlPanel(QWidget* parent)
    : QGroupBox("数据控制", parent)
{
    setupUi();
    setStyleSheet(R"(
        QGroupBox { font-weight: bold; border: 1px solid #3D3D3D; border-radius: 5px; margin-top: 10px; padding-top: 10px; background-color: #252526; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #CCCCCC; }
    )");
}

void DataControlPanel::setupUi() {
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setSpacing(5);

    // 数据点数标签
    m_countLabel = new QLabel("数据点数: 0");
    m_countLabel->setStyleSheet("color: #AAAAAA;");
    layout->addWidget(m_countLabel);

    // 按钮行
    QHBoxLayout* btnLayout = new QHBoxLayout();

    m_pauseBtn = new QPushButton("暂停");
    m_pauseBtn->setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 6px; }");
    connect(m_pauseBtn, &QPushButton::clicked, this, &DataControlPanel::onPauseClicked);
    btnLayout->addWidget(m_pauseBtn);

    m_clearBtn = new QPushButton("清空");
    m_clearBtn->setStyleSheet("QPushButton { background-color: #F44336; color: white; padding: 6px; }");
    connect(m_clearBtn, &QPushButton::clicked, this, &DataControlPanel::onClearClicked);
    btnLayout->addWidget(m_clearBtn);

    layout->addLayout(btnLayout);

    // 导出按钮
    m_exportBtn = new QPushButton("导出数据 (CSV)");
    m_exportBtn->setStyleSheet("QPushButton { background-color: #455A64; color: white; padding: 6px; }");
    connect(m_exportBtn, &QPushButton::clicked, this, &DataControlPanel::exportRequested);
    layout->addWidget(m_exportBtn);
}

void DataControlPanel::setDataCount(int count) {
    m_countLabel->setText(QString("数据点数: %1").arg(count));
}

void DataControlPanel::onPauseClicked() {
    m_isPaused = !m_isPaused;
    if (m_isPaused) {
        m_pauseBtn->setText("继续");
        m_pauseBtn->setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }");
    } else {
        m_pauseBtn->setText("暂停");
        m_pauseBtn->setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 6px; }");
    }
    emit pauseRequested(m_isPaused);
}

void DataControlPanel::onClearClicked() {
    emit clearRequested();
}
