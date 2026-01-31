/**
 * UnifiedDataProtocol.h - 统一数据协议
 *
 * 支持串口和UDP两种传输方式，使用相同的数据结构
 */

#ifndef UNIFIEDDATAPROTOCOL_H
#define UNIFIEDDATAPROTOCOL_H

#include <QString>
#include <QList>
#include <QVariantMap>
#include <optional>

/**
 * @brief 状态变量定义
 */
struct StateDefinition {
    int index = 0;
    QString name;
    QString unit;
    QString description;

    QVariantMap toVariantMap() const {
        return {
            {"index", index},
            {"name", name},
            {"unit", unit},
            {"description", description}
        };
    }
};

/**
 * @brief 状态值
 */
struct StateValue {
    double target = 0.0;
    double current = 0.0;

    double error() const { return target - current; }
};

/**
 * @brief 统一数据结构 - 串口和仿真共用
 */
struct UnifiedData {
    double timestamp = 0.0;     ///< 时间戳（秒）
    int seq = 0;                ///< 帧序号
    QList<StateValue> states;   ///< 状态值列表
    QString rawData;            ///< 原始数据（调试用）

    std::optional<StateValue> getState(int index) const {
        if (index >= 0 && index < states.size()) {
            return states[index];
        }
        return std::nullopt;
    }
};

/**
 * @brief 握手信息
 */
struct HandshakeInfo {
    int stateCount = 0;
    QList<StateDefinition> stateDefs;
    QString protocolVersion = "1.0";
    QString source = "serial";  ///< "serial" 或 "udp:system_type"
};

/**
 * @brief 串口协议解析器
 */
class SerialProtocolParser {
public:
    SerialProtocolParser() = default;

    /**
     * @brief 解析一行数据
     * @param line 输入行
     * @return (帧类型, 数据) 元组
     */
    std::pair<QString, std::optional<QVariant>> parseLine(const QString& line);

    /**
     * @brief 获取握手信息
     */
    const HandshakeInfo* handshake() const { return m_hasHandshake ? &m_handshake : nullptr; }

    /**
     * @brief 是否已收到握手
     */
    bool hasHandshake() const { return m_hasHandshake; }

    /**
     * @brief 重置解析器状态
     */
    void reset();

private:
    std::optional<HandshakeInfo> parseHandshake(const QString& line);
    std::optional<UnifiedData> parseDataFull(const QString& line);
    std::optional<UnifiedData> parseDataSimple(const QString& line);
    std::optional<UnifiedData> parseLegacy(const QString& line);

private:
    HandshakeInfo m_handshake;
    bool m_hasHandshake = false;
    QList<double> m_lastTargets;
    int m_seq = 0;
};

/**
 * @brief UDP JSON 协议解析器
 */
class UdpProtocolParser {
public:
    UdpProtocolParser() = default;

    /**
     * @brief 解析 JSON 数据包
     * @param jsonData JSON字节数据
     * @return (帧类型, 数据) 元组
     */
    std::pair<QString, std::optional<QVariant>> parsePacket(const QByteArray& jsonData);

    /**
     * @brief 获取握手信息
     */
    const HandshakeInfo* handshake() const { return m_hasHandshake ? &m_handshake : nullptr; }

    /**
     * @brief 重置解析器状态
     */
    void reset();

private:
    std::optional<HandshakeInfo> parseHandshake(const QVariantMap& payload);
    std::optional<UnifiedData> parseData(const QVariantMap& payload);

private:
    HandshakeInfo m_handshake;
    bool m_hasHandshake = false;
};

// 注册元类型以便在信号槽中使用
Q_DECLARE_METATYPE(UnifiedData)
Q_DECLARE_METATYPE(HandshakeInfo)
Q_DECLARE_METATYPE(StateDefinition)
Q_DECLARE_METATYPE(StateValue)

#endif // UNIFIEDDATAPROTOCOL_H
