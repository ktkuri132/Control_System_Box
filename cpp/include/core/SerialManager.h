/**
 * SerialManager.h - 串口通信管理模块
 */

#ifndef SERIALMANAGER_H
#define SERIALMANAGER_H

#include <QObject>
#include <QSerialPort>
#include <QThread>
#include <QMutex>
#include <memory>

#include "core/UnifiedDataProtocol.h"

/**
 * @brief 串口数据读取工作线程
 */
class SerialWorker : public QThread {
    Q_OBJECT

public:
    SerialWorker(const QString& port, int baudrate, QObject* parent = nullptr);
    ~SerialWorker() override;

    void stop();
    void sendData(const QString& data);

signals:
    void dataReceived(const UnifiedData& data);
    void handshakeReceived(const HandshakeInfo& info);
    void errorOccurred(const QString& message);
    void connectionLost();

protected:
    void run() override;

private:
    void processLine(const QString& line);
    void closeSerial();

private:
    QString m_port;
    int m_baudrate;
    bool m_running = false;
    QSerialPort* m_serial = nullptr;
    QMutex m_mutex;
    double m_startTime = 0.0;
    SerialProtocolParser m_parser;
    bool m_handshakeSent = false;
};

/**
 * @brief 串口管理器
 */
class SerialManager : public QObject {
    Q_OBJECT

public:
    explicit SerialManager(QObject* parent = nullptr);
    ~SerialManager() override;

    /**
     * @brief 获取可用串口列表
     * @return (设备名, 描述) 列表
     */
    static QList<QPair<QString, QString>> getAvailablePorts();

    /**
     * @brief 连接到串口
     * @param port 串口名
     * @param baudrate 波特率
     * @return 是否成功
     */
    bool connectToPort(const QString& port, int baudrate);

    /**
     * @brief 断开连接
     */
    void disconnect();

    /**
     * @brief 发送数据
     * @param data 数据字符串
     */
    void send(const QString& data);

    /**
     * @brief 是否已连接
     */
    bool isConnected() const { return m_connected; }

    /**
     * @brief 获取握手信息
     */
    const HandshakeInfo* handshakeInfo() const { return m_handshake.get(); }

signals:
    void dataReceived(const UnifiedData& data);
    void handshakeReceived(const HandshakeInfo& info);
    void connectionChanged(bool connected);
    void errorOccurred(const QString& message);

private slots:
    void onDataReceived(const UnifiedData& data);
    void onHandshakeReceived(const HandshakeInfo& info);
    void onError(const QString& message);
    void onConnectionLost();

private:
    std::unique_ptr<SerialWorker> m_worker;
    bool m_connected = false;
    std::unique_ptr<HandshakeInfo> m_handshake;
};

#endif // SERIALMANAGER_H
