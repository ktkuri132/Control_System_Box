/**
 * SerialManager.cpp - 串口通信管理实现
 */

#include "core/SerialManager.h"

#include <QSerialPortInfo>
#include <QElapsedTimer>
#include <QDebug>

// ============ SerialWorker 实现 ============

SerialWorker::SerialWorker(const QString& port, int baudrate, QObject* parent)
    : QThread(parent)
    , m_port(port)
    , m_baudrate(baudrate)
{
}

SerialWorker::~SerialWorker() {
    stop();
}

void SerialWorker::run() {
    QElapsedTimer timer;
    timer.start();

    try {
        m_serial = new QSerialPort();
        m_serial->setPortName(m_port);
        m_serial->setBaudRate(m_baudrate);
        m_serial->setDataBits(QSerialPort::Data8);
        m_serial->setParity(QSerialPort::NoParity);
        m_serial->setStopBits(QSerialPort::OneStop);

        if (!m_serial->open(QIODevice::ReadWrite)) {
            emit errorOccurred(QString("串口打开失败: %1").arg(m_serial->errorString()));
            closeSerial();
            return;
        }

        m_running = true;
        m_startTime = timer.elapsed() / 1000.0;
        m_parser.reset();

        QString buffer;

        while (m_running) {
            if (m_serial->waitForReadyRead(10)) {
                QByteArray data = m_serial->readAll();
                buffer += QString::fromUtf8(data);

                // 按行处理
                while (buffer.contains('\n')) {
                    int idx = buffer.indexOf('\n');
                    QString line = buffer.left(idx).trimmed();
                    buffer = buffer.mid(idx + 1);

                    if (!line.isEmpty()) {
                        processLine(line);
                    }
                }
            }
        }
    } catch (const std::exception& e) {
        emit errorOccurred(QString("串口错误: %1").arg(e.what()));
    }

    closeSerial();
}

void SerialWorker::processLine(const QString& line) {
    auto [frameType, data] = m_parser.parseLine(line);

    if (frameType == "handshake" && data.has_value()) {
        HandshakeInfo info = data->value<HandshakeInfo>();
        emit handshakeReceived(info);
    } else if (frameType == "data" && data.has_value()) {
        UnifiedData udata = data->value<UnifiedData>();

        // 如果是旧格式数据，补充时间戳
        if (udata.timestamp == 0.0) {
            QElapsedTimer timer;
            udata.timestamp = timer.elapsed() / 1000.0 - m_startTime;
        }

        emit dataReceived(udata);

        // 首次数据且自动生成了握手信息
        if (m_parser.handshake() && !m_handshakeSent) {
            m_handshakeSent = true;
            emit handshakeReceived(*m_parser.handshake());
        }
    }
}

void SerialWorker::stop() {
    m_running = false;
    if (!wait(2000)) {
        terminate();
        wait();
    }
    closeSerial();
}

void SerialWorker::closeSerial() {
    if (m_serial) {
        if (m_serial->isOpen()) {
            m_serial->close();
        }
        delete m_serial;
        m_serial = nullptr;
    }
}

void SerialWorker::sendData(const QString& data) {
    QMutexLocker locker(&m_mutex);
    if (m_serial && m_serial->isOpen()) {
        m_serial->write((data + "\n").toUtf8());
        m_serial->flush();
    }
}

// ============ SerialManager 实现 ============

SerialManager::SerialManager(QObject* parent)
    : QObject(parent)
{
    // 注册元类型
    qRegisterMetaType<UnifiedData>("UnifiedData");
    qRegisterMetaType<HandshakeInfo>("HandshakeInfo");
}

SerialManager::~SerialManager() {
    disconnect();
}

QList<QPair<QString, QString>> SerialManager::getAvailablePorts() {
    QList<QPair<QString, QString>> ports;

    for (const QSerialPortInfo& info : QSerialPortInfo::availablePorts()) {
        QString description = QString("%1 - %2").arg(info.portName(), info.description());
        ports.append({info.portName(), description});
    }

    return ports;
}

bool SerialManager::connectToPort(const QString& port, int baudrate) {
    if (m_connected) {
        disconnect();
    }

    m_worker = std::make_unique<SerialWorker>(port, baudrate);

    connect(m_worker.get(), &SerialWorker::dataReceived,
            this, &SerialManager::onDataReceived);
    connect(m_worker.get(), &SerialWorker::handshakeReceived,
            this, &SerialManager::onHandshakeReceived);
    connect(m_worker.get(), &SerialWorker::errorOccurred,
            this, &SerialManager::onError);
    connect(m_worker.get(), &SerialWorker::connectionLost,
            this, &SerialManager::onConnectionLost);

    m_worker->start();
    m_connected = true;
    emit connectionChanged(true);

    return true;
}

void SerialManager::disconnect() {
    if (m_worker) {
        m_worker->stop();
        m_worker.reset();
    }
    m_connected = false;
    m_handshake.reset();
    emit connectionChanged(false);
}

void SerialManager::send(const QString& data) {
    if (m_worker) {
        m_worker->sendData(data);
    }
}

void SerialManager::onDataReceived(const UnifiedData& data) {
    emit dataReceived(data);
}

void SerialManager::onHandshakeReceived(const HandshakeInfo& info) {
    m_handshake = std::make_unique<HandshakeInfo>(info);
    emit handshakeReceived(info);
}

void SerialManager::onError(const QString& message) {
    emit errorOccurred(message);
}

void SerialManager::onConnectionLost() {
    m_connected = false;
    m_handshake.reset();
    emit connectionChanged(false);
}
