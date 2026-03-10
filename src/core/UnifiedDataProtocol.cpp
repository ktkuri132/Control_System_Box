/**
 * UnifiedDataProtocol.cpp - 统一数据协议实现
 */

#include "core/UnifiedDataProtocol.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QRegularExpression>

// ============ SerialProtocolParser 实现 ============

std::pair<QString, std::optional<QVariant>> SerialProtocolParser::parseLine(const QString& line) {
    QString trimmed = line.trimmed();
    if (trimmed.isEmpty()) {
        return {"", std::nullopt};
    }

    // 检查帧标识
    if (trimmed.startsWith("#H,") || trimmed.startsWith("#h,")) {
        auto info = parseHandshake(trimmed);
        if (info) {
            return {"handshake", QVariant::fromValue(*info)};
        }
    } else if (trimmed.startsWith("#D,")) {
        auto data = parseDataFull(trimmed);
        if (data) {
            return {"data", QVariant::fromValue(*data)};
        }
    } else if (trimmed.startsWith("#d,")) {
        auto data = parseDataSimple(trimmed);
        if (data) {
            return {"data", QVariant::fromValue(*data)};
        }
    } else {
        // 尝试旧格式兼容
        auto data = parseLegacy(trimmed);
        if (data) {
            return {"data", QVariant::fromValue(*data)};
        }
    }

    return {"", std::nullopt};
}

std::optional<HandshakeInfo> SerialProtocolParser::parseHandshake(const QString& line) {
    try {
        QStringList parts = line.mid(3).split(',');
        if (parts.isEmpty()) return std::nullopt;

        int stateCount = parts[0].toInt();

        QList<StateDefinition> stateDefs;
        for (int i = 0; i < stateCount && i + 1 < parts.size(); ++i) {
            QString name = parts[i + 1].trimmed();
            QString unit;

            // 解析名称和单位: "angle(rad)" -> name="angle", unit="rad"
            int parenIdx = name.indexOf('(');
            if (parenIdx != -1 && name.endsWith(')')) {
                unit = name.mid(parenIdx + 1, name.length() - parenIdx - 2);
                name = name.left(parenIdx);
            }

            StateDefinition def;
            def.index = i;
            def.name = name;
            def.unit = unit;
            stateDefs.append(def);
        }

        m_handshake.stateCount = stateCount;
        m_handshake.stateDefs = stateDefs;
        m_handshake.protocolVersion = "1.0";
        m_handshake.source = "serial";
        m_hasHandshake = true;

        // 初始化目标值缓存
        m_lastTargets.clear();
        for (int i = 0; i < stateCount; ++i) {
            m_lastTargets.append(0.0);
        }

        return m_handshake;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<UnifiedData> SerialProtocolParser::parseDataFull(const QString& line) {
    try {
        QStringList parts = line.mid(3).split(',');
        if (parts.size() < 3) return std::nullopt;

        int seq = parts[0].toInt();
        int timeMs = parts[1].toInt();
        double timestamp = timeMs / 1000.0;

        QList<StateValue> states;
        for (int i = 2; i + 1 < parts.size(); i += 2) {
            double target = parts[i].toDouble();
            double current = parts[i + 1].toDouble();

            StateValue sv;
            sv.target = target;
            sv.current = current;
            states.append(sv);

            // 更新目标值缓存
            int idx = (i - 2) / 2;
            if (idx < m_lastTargets.size()) {
                m_lastTargets[idx] = target;
            }
        }

        m_seq = seq;

        UnifiedData data;
        data.timestamp = timestamp;
        data.seq = seq;
        data.states = states;
        data.rawData = line;

        return data;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<UnifiedData> SerialProtocolParser::parseDataSimple(const QString& line) {
    try {
        QStringList parts = line.mid(3).split(',');
        if (parts.size() < 3) return std::nullopt;

        int seq = parts[0].toInt();
        int timeMs = parts[1].toInt();
        double timestamp = timeMs / 1000.0;

        QList<StateValue> states;
        for (int i = 2; i < parts.size(); ++i) {
            double current = parts[i].toDouble();
            double target = (i - 2 < m_lastTargets.size()) ? m_lastTargets[i - 2] : 0.0;

            StateValue sv;
            sv.target = target;
            sv.current = current;
            states.append(sv);
        }

        m_seq = seq;

        UnifiedData data;
        data.timestamp = timestamp;
        data.seq = seq;
        data.states = states;
        data.rawData = line;

        return data;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<UnifiedData> SerialProtocolParser::parseLegacy(const QString& line) {
    try {
        QList<StateValue> states;

        // 尝试格式1: SP:100,PV:95.5,OUT:50
        if (line.contains(':')) {
            QStringList parts = line.split(',');
            double sp = 0, pv = 0, out = 0;

            for (const QString& part : parts) {
                if (part.startsWith("SP:", Qt::CaseInsensitive)) {
                    sp = part.mid(3).toDouble();
                } else if (part.startsWith("PV:", Qt::CaseInsensitive)) {
                    pv = part.mid(3).toDouble();
                } else if (part.startsWith("OUT:", Qt::CaseInsensitive)) {
                    out = part.mid(4).toDouble();
                }
            }

            // 创建单状态
            StateValue sv;
            sv.target = sp;
            sv.current = pv;
            states.append(sv);

            // 输出作为第二个状态
            StateValue svOut;
            svOut.target = 0;
            svOut.current = out;
            states.append(svOut);
        } else {
            // 尝试格式2: 100,95.5,50 (纯数值)
            QStringList parts = line.split(',');
            if (parts.size() >= 2) {
                for (int i = 0; i + 1 < parts.size(); i += 2) {
                    StateValue sv;
                    sv.target = parts[i].toDouble();
                    sv.current = parts[i + 1].toDouble();
                    states.append(sv);
                }

                // 如果是奇数个，最后一个作为输出
                if (parts.size() % 2 == 1) {
                    StateValue sv;
                    sv.target = 0;
                    sv.current = parts.last().toDouble();
                    states.append(sv);
                }
            }
        }

        if (states.isEmpty()) {
            return std::nullopt;
        }

        // 如果没有握手信息，自动生成
        if (!m_hasHandshake) {
            m_handshake.stateCount = states.size();
            m_handshake.stateDefs.clear();

            QStringList defaultNames = {"SP/PV", "Output", "State3", "State4", "State5"};
            for (int i = 0; i < states.size() && i < defaultNames.size(); ++i) {
                StateDefinition def;
                def.index = i;
                def.name = defaultNames[i];
                m_handshake.stateDefs.append(def);
            }

            m_handshake.protocolVersion = "0.9";
            m_handshake.source = "serial:legacy";
            m_hasHandshake = true;
        }

        m_seq++;

        UnifiedData data;
        data.timestamp = 0.0;  // 需要在外部补充
        data.seq = m_seq;
        data.states = states;
        data.rawData = line;

        return data;
    } catch (...) {
        return std::nullopt;
    }
}

void SerialProtocolParser::reset() {
    m_hasHandshake = false;
    m_handshake = HandshakeInfo();
    m_lastTargets.clear();
    m_seq = 0;
}

// ============ UdpProtocolParser 实现 ============

std::pair<QString, std::optional<QVariant>> UdpProtocolParser::parsePacket(const QByteArray& jsonData) {
    QJsonParseError error;
    QJsonDocument doc = QJsonDocument::fromJson(jsonData, &error);

    if (error.error != QJsonParseError::NoError) {
        return {"", std::nullopt};
    }

    QVariantMap payload = doc.object().toVariantMap();
    QString frameType = payload.value("frame_type").toString();

    if (frameType == "HANDSHAKE") {
        auto info = parseHandshake(payload);
        if (info) {
            return {"handshake", QVariant::fromValue(*info)};
        }
    } else if (frameType == "DATA") {
        auto data = parseData(payload);
        if (data) {
            return {"data", QVariant::fromValue(*data)};
        }
    }

    return {"", std::nullopt};
}

std::optional<HandshakeInfo> UdpProtocolParser::parseHandshake(const QVariantMap& payload) {
    try {
        QString systemType = payload.value("system_type", "unknown").toString();

        QList<StateDefinition> stateDefs;
        QVariantList states = payload.value("states").toList();

        for (const QVariant& stateVar : states) {
            QVariantMap state = stateVar.toMap();
            StateDefinition def;
            def.index = state.value("index", stateDefs.size()).toInt();
            def.name = state.value("name", QString("state_%1").arg(stateDefs.size())).toString();
            def.unit = state.value("unit").toString();
            def.description = state.value("description").toString();
            stateDefs.append(def);
        }

        m_handshake.stateCount = payload.value("state_count", stateDefs.size()).toInt();
        m_handshake.stateDefs = stateDefs;
        m_handshake.protocolVersion = payload.value("version", "2.0").toString();
        m_handshake.source = QString("udp:%1").arg(systemType);
        m_hasHandshake = true;

        return m_handshake;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<UnifiedData> UdpProtocolParser::parseData(const QVariantMap& payload) {
    if (!m_hasHandshake) {
        return std::nullopt;
    }

    try {
        QList<StateValue> states;
        QVariantList statesRaw = payload.value("states").toList();

        for (const QVariant& stateVar : statesRaw) {
            QVariantMap state = stateVar.toMap();
            StateValue sv;
            sv.target = state.value("target", 0.0).toDouble();
            sv.current = state.value("current", 0.0).toDouble();
            states.append(sv);
        }

        UnifiedData data;
        data.timestamp = payload.value("sim_time", 0.0).toDouble();
        data.seq = payload.value("seq", 0).toInt();
        data.states = states;

        return data;
    } catch (...) {
        return std::nullopt;
    }
}

void UdpProtocolParser::reset() {
    m_hasHandshake = false;
    m_handshake = HandshakeInfo();
}
