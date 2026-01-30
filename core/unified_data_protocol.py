"""
统一数据协议模块
支持串口和UDP两种传输方式，使用相同的数据结构

串口协议设计（高效、实时）：
=========================================

【握手帧】 - 首次连接或配置改变时发送
格式: #H,<状态数>,<状态1名称>,<状态2名称>,...\n
示例: #H,3,angle,position,force\n

【数据帧】 - 高频发送 (100Hz+)
格式: #D,<序号>,<时间ms>,<目标1>,<当前1>,<目标2>,<当前2>,...\n
示例: #D,1234,15000,0.00,0.05,0.00,-0.02,0.00,2.50\n

【简化数据帧】 - 当目标值不变时可省略
格式: #d,<序号>,<时间ms>,<当前1>,<当前2>,...\n
示例: #d,1234,15000,0.05,-0.02,2.50\n

【二进制数据帧】 - 更高效率 (可选)
格式: 0xAA <len> <seq:2> <time:4> <data:4*N> <checksum>\n
      帧头  长度   序号    时间ms   浮点数据    校验和

协议特点：
- 文本格式便于调试，二进制格式更高效
- 握手帧声明状态变量，数据帧只传数值
- 支持可变状态数量
- 校验和可选，提高可靠性
"""

import struct
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class FrameType(Enum):
    """帧类型"""
    HANDSHAKE = "H"      # 握手帧
    DATA = "D"           # 完整数据帧 (target + current)
    DATA_SIMPLE = "d"    # 简化数据帧 (仅 current)
    BINARY = 0xAA        # 二进制数据帧


@dataclass
class StateDefinition:
    """状态变量定义"""
    index: int
    name: str
    unit: str = ""
    description: str = ""


@dataclass
class StateValue:
    """状态值"""
    target: float
    current: float

    @property
    def error(self) -> float:
        return self.target - self.current


@dataclass
class UnifiedData:
    """统一数据结构 - 串口和仿真共用"""
    timestamp: float          # 时间戳（秒）
    seq: int                  # 帧序号
    states: List[StateValue]  # 状态值列表
    raw_data: str = ""        # 原始数据（调试用）

    def get_state(self, index: int) -> Optional[StateValue]:
        """获取指定索引的状态"""
        if 0 <= index < len(self.states):
            return self.states[index]
        return None


@dataclass
class HandshakeInfo:
    """握手信息"""
    state_count: int
    state_defs: List[StateDefinition] = field(default_factory=list)
    protocol_version: str = "1.0"
    source: str = "serial"  # "serial" or "udp"


class SerialProtocolParser:
    """串口协议解析器"""

    def __init__(self):
        self._handshake: Optional[HandshakeInfo] = None
        self._last_targets: List[float] = []  # 缓存上次的目标值
        self._seq = 0

    @property
    def handshake(self) -> Optional[HandshakeInfo]:
        return self._handshake

    @property
    def has_handshake(self) -> bool:
        return self._handshake is not None

    def parse_line(self, line: str) -> Tuple[Optional[str], Optional[object]]:
        """
        解析一行数据
        返回: (帧类型, 数据对象) 或 (None, None) 如果解析失败
        """
        line = line.strip()
        if not line:
            return None, None

        # 检查帧标识
        if line.startswith('#H,') or line.startswith('#h,'):
            return 'handshake', self._parse_handshake(line)
        elif line.startswith('#D,'):
            return 'data', self._parse_data_full(line)
        elif line.startswith('#d,'):
            return 'data', self._parse_data_simple(line)
        elif line[0:1] == chr(0xAA):
            return 'data', self._parse_binary(line.encode('latin-1'))
        else:
            # 尝试兼容旧格式
            return 'data', self._parse_legacy(line)

    def _parse_handshake(self, line: str) -> Optional[HandshakeInfo]:
        """解析握手帧: #H,<状态数>,<名称1>,<名称2>,..."""
        try:
            parts = line[3:].split(',')
            state_count = int(parts[0])

            state_defs = []
            for i in range(state_count):
                name = parts[i + 1] if i + 1 < len(parts) else f"state_{i}"
                # 解析名称和单位: "angle(rad)" -> name="angle", unit="rad"
                unit = ""
                if '(' in name and ')' in name:
                    idx = name.index('(')
                    unit = name[idx+1:-1]
                    name = name[:idx]

                state_defs.append(StateDefinition(
                    index=i,
                    name=name.strip(),
                    unit=unit,
                    description=""
                ))

            self._handshake = HandshakeInfo(
                state_count=state_count,
                state_defs=state_defs,
                protocol_version="1.0",
                source="serial"
            )
            # 初始化目标值缓存
            self._last_targets = [0.0] * state_count

            return self._handshake

        except (ValueError, IndexError) as e:
            return None

    def _parse_data_full(self, line: str) -> Optional[UnifiedData]:
        """解析完整数据帧: #D,<seq>,<time_ms>,<t1>,<c1>,<t2>,<c2>,..."""
        try:
            parts = line[3:].split(',')
            seq = int(parts[0])
            time_ms = int(parts[1])
            timestamp = time_ms / 1000.0

            # 解析状态值对 (target, current)
            values = [float(v) for v in parts[2:]]
            states = []
            for i in range(0, len(values), 2):
                if i + 1 < len(values):
                    target = values[i]
                    current = values[i + 1]
                    states.append(StateValue(target=target, current=current))
                    # 更新目标值缓存
                    idx = i // 2
                    if idx < len(self._last_targets):
                        self._last_targets[idx] = target

            self._seq = seq
            return UnifiedData(
                timestamp=timestamp,
                seq=seq,
                states=states,
                raw_data=line
            )

        except (ValueError, IndexError):
            return None

    def _parse_data_simple(self, line: str) -> Optional[UnifiedData]:
        """解析简化数据帧: #d,<seq>,<time_ms>,<c1>,<c2>,..."""
        try:
            parts = line[3:].split(',')
            seq = int(parts[0])
            time_ms = int(parts[1])
            timestamp = time_ms / 1000.0

            # 解析当前值，目标值使用缓存
            currents = [float(v) for v in parts[2:]]
            states = []
            for i, current in enumerate(currents):
                target = self._last_targets[i] if i < len(self._last_targets) else 0.0
                states.append(StateValue(target=target, current=current))

            self._seq = seq
            return UnifiedData(
                timestamp=timestamp,
                seq=seq,
                states=states,
                raw_data=line
            )

        except (ValueError, IndexError):
            return None

    def _parse_binary(self, data: bytes) -> Optional[UnifiedData]:
        """解析二进制数据帧"""
        try:
            if len(data) < 8:
                return None

            # 0xAA <len> <seq:2> <time:4> <data:4*N> [checksum]
            header = data[0]
            length = data[1]
            seq = struct.unpack('<H', data[2:4])[0]
            time_ms = struct.unpack('<I', data[4:8])[0]
            timestamp = time_ms / 1000.0

            # 解析浮点数据
            float_data = data[8:8 + length - 6]
            num_floats = len(float_data) // 4
            values = struct.unpack(f'<{num_floats}f', float_data[:num_floats * 4])

            # 每两个值一组 (target, current)
            states = []
            for i in range(0, len(values), 2):
                if i + 1 < len(values):
                    states.append(StateValue(target=values[i], current=values[i + 1]))

            return UnifiedData(
                timestamp=timestamp,
                seq=seq,
                states=states,
                raw_data=data.hex()
            )

        except (struct.error, IndexError):
            return None

    def _parse_legacy(self, line: str) -> Optional[UnifiedData]:
        """解析旧格式（向后兼容）"""
        try:
            # 支持: "SP:100,PV:95.5,OUT:50" 或 "100,95.5,50"
            sp, pv, out = 0.0, 0.0, 0.0

            if ':' in line or '=' in line:
                # 键值对格式
                parts = {}
                for item in line.replace(' ', '').split(','):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        parts[key.upper()] = float(value)
                    elif '=' in item:
                        key, value = item.split('=', 1)
                        parts[key.upper()] = float(value)

                sp = parts.get('SP', parts.get('SETPOINT', 0.0))
                pv = parts.get('PV', parts.get('PROCESS', 0.0))
                out = parts.get('OUT', parts.get('OUTPUT', 0.0))
            else:
                # CSV格式
                values = [float(v.strip()) for v in line.split(',') if v.strip()]
                if len(values) >= 3:
                    sp, pv, out = values[0], values[1], values[2]
                elif len(values) == 2:
                    sp, pv = values[0], values[1]
                elif len(values) == 1:
                    pv = values[0]

            # 如果没有握手信息，创建默认的
            if not self._handshake:
                self._handshake = HandshakeInfo(
                    state_count=3,
                    state_defs=[
                        StateDefinition(0, "setpoint", "", "设定值"),
                        StateDefinition(1, "process_value", "", "过程值"),
                        StateDefinition(2, "control_output", "", "控制输出"),
                    ],
                    source="serial"
                )
                self._last_targets = [sp, 0.0, 0.0]

            self._seq += 1
            return UnifiedData(
                timestamp=0.0,  # 旧格式没有时间戳，由接收端计算
                seq=self._seq,
                states=[
                    StateValue(target=sp, current=pv),
                    StateValue(target=0.0, current=out),
                ],
                raw_data=line
            )

        except (ValueError, IndexError):
            return None

    def reset(self):
        """重置解析器状态"""
        self._handshake = None
        self._last_targets = []
        self._seq = 0


def generate_handshake_frame(state_names: List[str]) -> str:
    """生成握手帧字符串"""
    return f"#H,{len(state_names)},{','.join(state_names)}\n"


def generate_data_frame(seq: int, time_ms: int, states: List[Tuple[float, float]]) -> str:
    """生成完整数据帧字符串"""
    values = []
    for target, current in states:
        values.append(f"{target:.4f}")
        values.append(f"{current:.4f}")
    return f"#D,{seq},{time_ms},{','.join(values)}\n"


def generate_simple_data_frame(seq: int, time_ms: int, currents: List[float]) -> str:
    """生成简化数据帧字符串"""
    values = [f"{c:.4f}" for c in currents]
    return f"#d,{seq},{time_ms},{','.join(values)}\n"
