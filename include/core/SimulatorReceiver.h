/**
 * SimulatorReceiver.h - UDP仿真数据接收模块
 */

#ifndef SIMULATORRECEIVER_H
#define SIMULATORRECEIVER_H

#include <QObject>
#include <QThread>
#include <QUdpSocket>
#include <memory>

#include "core/UnifiedDataProtocol.h"

/**
 * @brief UDP数据接收工作线程
 */
class UDPReceiverWorker : public QThread {
    Q_OBJECT

public:
    UDPReceiverWorker(const QString& host, int port, QObject* parent = nullptr);
    ~UDPReceiverWorker() override;

    void stop();

signals:
    void dataReceived(const UnifiedData& data);
    void handshakeReceived(const HandshakeInfo& info);
    void errorOccurred(const QString& message);
    void connectionStatus(bool connected, const QString& message);

protected:
    void run() override;

private:
    void processPacket(const QByteArray& data);
    void closeSocket();

private:
    QString m_host;
    int m_port;
    bool m_running = false;
    QUdpSocket* m_socket = nullptr;
    UdpProtocolParser m_parser;
};

/**
 * @brief 仿真数据接收管理器
 */
class SimulatorReceiver : public QObject {
    Q_OBJECT

public:
    explicit SimulatorReceiver(QObject* parent = nullptr);
    ~SimulatorReceiver() override;

    /**
     * @brief 开始接收仿真数据
     * @param host 主机地址
     * @param port 端口号
     * @return 是否成功
     */
    bool start(const QString& host = "127.0.0.1", int port = 5555);

    /**
     * @brief 停止接收
     */
    void stop();

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
    void connectionChanged(bool connected, const QString& message);
    void errorOccurred(const QString& message);

private slots:
    void onDataReceived(const UnifiedData& data);
    void onHandshakeReceived(const HandshakeInfo& info);
    void onError(const QString& message);
    void onConnectionStatus(bool connected, const QString& message);

private:
    std::unique_ptr<UDPReceiverWorker> m_worker;
    bool m_connected = false;
    std::unique_ptr<HandshakeInfo> m_handshake;
};

#endif // SIMULATORRECEIVER_H
