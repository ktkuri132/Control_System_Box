"""
UDP 仿真数据接收模块 (统一协议版本)
支持 JSON 格式的协议 v2.0，输出统一数据结构
"""
import socket
import json
import math
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from typing import Optional, List
from enum import Enum

from core.unified_data_protocol import (
    UnifiedData, HandshakeInfo, StateDefinition, StateValue
)


class SimulationSystemType(Enum):
    """仿真系统类型"""
    INVERTED_PENDULUM = "inverted_pendulum"
    BALL_ON_PLATE = "ball_on_plate"
    UNKNOWN = "unknown"


class UDPReceiverWorker(QThread):
    """UDP数据接收工作线程"""
    data_received = pyqtSignal(object)       # UnifiedData
    handshake_received = pyqtSignal(object)  # HandshakeInfo
    error_occurred = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        super().__init__()
        self.host = host
        self.port = port
        self._running = False
        self._socket: Optional[socket.socket] = None
        self._handshake: Optional[HandshakeInfo] = None
        self._state_defs: List[StateDefinition] = []

    def run(self):
        """线程主循环"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.host, self.port))
            self._socket.settimeout(0.5)

            self._running = True
            self.connection_status.emit(True, f"正在监听 {self.host}:{self.port}")
            
            while self._running:
                try:
                    data, addr = self._socket.recvfrom(4096)
                    self._process_packet(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        self.error_occurred.emit(f"接收错误: {str(e)}")
                        
        except Exception as e:
            self.error_occurred.emit(f"UDP绑定失败: {str(e)}")
            self.connection_status.emit(False, f"绑定失败: {str(e)}")
        finally:
            self._close_socket()
    
    def _process_packet(self, data: bytes):
        """处理接收到的数据包"""
        try:
            payload = json.loads(data.decode('utf-8'))
            frame_type = payload.get('frame_type', '')

            if frame_type == 'HANDSHAKE':
                self._process_handshake(payload)
            elif frame_type == 'DATA':
                self._process_data(payload)

        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"JSON解析错误: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"数据处理错误: {str(e)}")
    
    def _process_handshake(self, payload: dict):
        """处理握手帧"""
        try:
            system_type = payload.get('system_type', 'unknown')

            state_defs = []
            for state in payload.get('states', []):
                state_defs.append(StateDefinition(
                    index=state.get('index', len(state_defs)),
                    name=state.get('name', f'state_{len(state_defs)}'),
                    unit=state.get('unit', ''),
                    description=state.get('description', '')
                ))

            self._handshake = HandshakeInfo(
                state_count=payload.get('state_count', len(state_defs)),
                state_defs=state_defs,
                protocol_version=payload.get('version', '2.0'),
                source=f"udp:{system_type}"
            )
            self._state_defs = state_defs

            self.handshake_received.emit(self._handshake)

        except Exception as e:
            self.error_occurred.emit(f"握手帧解析错误: {str(e)}")

    def _process_data(self, payload: dict):
        """处理数据帧"""
        if not self._handshake:
            return

        try:
            states_raw = payload.get('states', [])
            states = []
            for s in states_raw:
                states.append(StateValue(
                    target=s.get('target', 0.0),
                    current=s.get('current', 0.0)
                ))

            unified_data = UnifiedData(
                timestamp=payload.get('sim_time', 0.0),
                seq=payload.get('seq', 0),
                states=states,
                raw_data=str(payload)
            )

            self.data_received.emit(unified_data)

        except Exception as e:
            self.error_occurred.emit(f"数据帧解析错误: {str(e)}")

    def _close_socket(self):
        """关闭套接字"""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
    
    def stop(self):
        """停止接收"""
        self._running = False
        self.wait(2000)
        self._close_socket()
        self.connection_status.emit(False, "已停止监听")


class SimulatorReceiver(QObject):
    """仿真数据接收管理器"""
    data_received = pyqtSignal(object)       # UnifiedData
    handshake_received = pyqtSignal(object)  # HandshakeInfo
    connection_changed = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._worker: Optional[UDPReceiverWorker] = None
        self._is_connected = False
        self._handshake: Optional[HandshakeInfo] = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def handshake_info(self) -> Optional[HandshakeInfo]:
        return self._handshake

    def start(self, host: str = "127.0.0.1", port: int = 5555) -> bool:
        """开始接收仿真数据"""
        if self._is_connected:
            self.stop()
        
        self._worker = UDPReceiverWorker(host, port)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.handshake_received.connect(self._on_handshake_received)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.connection_status.connect(self._on_connection_status)
        self._worker.start()
        
        return True
    
    def stop(self):
        """停止接收"""
        if self._worker:
            self._worker.stop()
            self._worker = None
        self._is_connected = False
        self._handshake = None
        self.connection_changed.emit(False, "已停止")
    
    def _on_data_received(self, data: UnifiedData):
        self.data_received.emit(data)
    
    def _on_handshake_received(self, handshake: HandshakeInfo):
        self._handshake = handshake
        self.handshake_received.emit(handshake)

    def _on_error(self, message: str):
        self.error_occurred.emit(message)
    
    def _on_connection_status(self, connected: bool, message: str):
        self._is_connected = connected
        self.connection_changed.emit(connected, message)
