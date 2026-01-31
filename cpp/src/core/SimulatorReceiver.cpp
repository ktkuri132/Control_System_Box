/**
 * SimulatorReceiver.cpp - UDP仿真数据接收实现
 */

#include "core/SimulatorReceiver.h"

#include <QJsonDocument>
#include <QDebug>

// ============ UDPReceiverWorker 实现 ============

UDPReceiverWorker::UDPReceiverWorker(const QString& host, int port, QObject* parent)
    : QThread(parent)
    , m_host(host)
    , m_port(port)
{
}

UDPReceiverWorker::~UDPReceiverWorker() {
    stop();
}

void UDPReceiverWorker::run() {
    m_socket = new QUdpSocket();

    if (!m_socket->bind(QHostAddress(m_host), m_port, QUdpSocket::ShareAddress)) {
        emit errorOccurred(QString("UDP绑定失败: %1").arg(m_socket->errorString()));
        emit connectionStatus(false, QString("绑定失败: %1").arg(m_socket->errorString()));
        closeSocket();
        return;
    }

    m_running = true;
    emit connectionStatus(true, QString("正在监听 %1:%2").arg(m_host).arg(m_port));

    while (m_running) {
        if (m_socket->waitForReadyRead(500)) {
            while (m_socket->hasPendingDatagrams()) {
                QByteArray data;
                data.resize(m_socket->pendingDatagramSize());
                m_socket->readDatagram(data.data(), data.size());
                processPacket(data);
            }
        }
    }

    closeSocket();
}

void UDPReceiverWorker::processPacket(const QByteArray& data) {
    auto [frameType, result] = m_parser.parsePacket(data);

    if (frameType == "handshake" && result.has_value()) {
        HandshakeInfo info = result->value<HandshakeInfo>();
        emit handshakeReceived(info);
    } else if (frameType == "data" && result.has_value()) {
        UnifiedData udata = result->value<UnifiedData>();
        emit dataReceived(udata);
    }
}

void UDPReceiverWorker::stop() {
    m_running = false;
    if (!wait(2000)) {
        terminate();
        wait();
    }
    closeSocket();
    emit connectionStatus(false, "已停止监听");
}

void UDPReceiverWorker::closeSocket() {
    if (m_socket) {
        m_socket->close();
        delete m_socket;
        m_socket = nullptr;
    }
}

// ============ SimulatorReceiver 实现 ============

SimulatorReceiver::SimulatorReceiver(QObject* parent)
    : QObject(parent)
{
    qRegisterMetaType<UnifiedData>("UnifiedData");
    qRegisterMetaType<HandshakeInfo>("HandshakeInfo");
}

SimulatorReceiver::~SimulatorReceiver() {
    stop();
}

bool SimulatorReceiver::start(const QString& host, int port) {
    if (m_connected) {
        stop();
    }

    m_worker = std::make_unique<UDPReceiverWorker>(host, port);

    connect(m_worker.get(), &UDPReceiverWorker::dataReceived,
            this, &SimulatorReceiver::onDataReceived);
    connect(m_worker.get(), &UDPReceiverWorker::handshakeReceived,
            this, &SimulatorReceiver::onHandshakeReceived);
    connect(m_worker.get(), &UDPReceiverWorker::errorOccurred,
            this, &SimulatorReceiver::onError);
    connect(m_worker.get(), &UDPReceiverWorker::connectionStatus,
            this, &SimulatorReceiver::onConnectionStatus);

    m_worker->start();

    return true;
}

void SimulatorReceiver::stop() {
    if (m_worker) {
        m_worker->stop();
        m_worker.reset();
    }
    m_connected = false;
    m_handshake.reset();
    emit connectionChanged(false, "已停止");
}

void SimulatorReceiver::onDataReceived(const UnifiedData& data) {
    emit dataReceived(data);
}

void SimulatorReceiver::onHandshakeReceived(const HandshakeInfo& info) {
    m_handshake = std::make_unique<HandshakeInfo>(info);
    emit handshakeReceived(info);
}

void SimulatorReceiver::onError(const QString& message) {
    emit errorOccurred(message);
}

void SimulatorReceiver::onConnectionStatus(bool connected, const QString& message) {
    m_connected = connected;
    emit connectionChanged(connected, message);
}
