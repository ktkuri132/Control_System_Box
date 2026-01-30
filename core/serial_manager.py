"""
串口通信管理模块 (统一协议版本)
支持新的高效协议和旧格式兼容
"""
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex
from typing import Optional
import time

from core.unified_data_protocol import (
    SerialProtocolParser, UnifiedData, HandshakeInfo,
    StateDefinition, StateValue
)


class SerialWorker(QThread):
    """串口数据读取工作线程"""
    data_received = pyqtSignal(object)      # UnifiedData
    handshake_received = pyqtSignal(object)  # HandshakeInfo
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()
    
    def __init__(self, port: str, baudrate: int):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._running = False
        self._serial: Optional[serial.Serial] = None
        self._mutex = QMutex()
        self._start_time = 0.0
        self._parser = SerialProtocolParser()

    def run(self):
        """线程主循环"""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self._running = True
            self._start_time = time.time()
            self._parser.reset()

            buffer = ""
            while self._running:
                if self._serial and self._serial.in_waiting:
                    try:
                        # 读取可用数据
                        chunk = self._serial.read(self._serial.in_waiting)
                        buffer += chunk.decode('utf-8', errors='ignore')
                        
                        # 按行处理
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                self._process_line(line)

                    except serial.SerialException as e:
                        self.error_occurred.emit(f"读取错误: {str(e)}")
                        self.connection_lost.emit()
                        break
                else:
                    self.msleep(1)

        except serial.SerialException as e:
            self.error_occurred.emit(f"串口打开失败: {str(e)}")
        finally:
            self._close_serial()
    
    def _process_line(self, line: str):
        """处理一行数据"""
        frame_type, data = self._parser.parse_line(line)

        if frame_type == 'handshake' and data:
            self.handshake_received.emit(data)
        elif frame_type == 'data' and data:
            # 如果是旧格式数据，补充时间戳
            if data.timestamp == 0.0:
                data.timestamp = time.time() - self._start_time
            self.data_received.emit(data)

            # 如果是首次数据且解析器自动生成了握手信息
            if self._parser.handshake and not hasattr(self, '_handshake_sent'):
                self._handshake_sent = True
                self.handshake_received.emit(self._parser.handshake)

    def _close_serial(self):
        """关闭串口"""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except:
                pass
        self._serial = None
    
    def stop(self):
        """停止线程"""
        self._running = False
        self.wait(2000)
        self._close_serial()
    
    def send_data(self, data: str):
        """发送数据到串口"""
        self._mutex.lock()
        try:
            if self._serial and self._serial.is_open:
                self._serial.write((data + '\n').encode('utf-8'))
                self._serial.flush()
        except serial.SerialException as e:
            self.error_occurred.emit(f"发送失败: {str(e)}")
        finally:
            self._mutex.unlock()


class SerialManager(QObject):
    """串口管理器"""
    data_received = pyqtSignal(object)       # UnifiedData
    handshake_received = pyqtSignal(object)  # HandshakeInfo
    connection_changed = pyqtSignal(bool)    # True=已连接, False=已断开
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._worker: Optional[SerialWorker] = None
        self._is_connected = False
        self._handshake: Optional[HandshakeInfo] = None

    @staticmethod
    def get_available_ports() -> list[tuple[str, str]]:
        """获取可用串口列表"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, f"{port.device} - {port.description}"))
        return ports
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def handshake_info(self) -> Optional[HandshakeInfo]:
        return self._handshake

    def connect(self, port: str, baudrate: int) -> bool:
        """连接串口"""
        if self._is_connected:
            self.disconnect()
        
        self._worker = SerialWorker(port, baudrate)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.handshake_received.connect(self._on_handshake_received)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.connection_lost.connect(self._on_connection_lost)
        self._worker.start()
        
        self._is_connected = True
        self.connection_changed.emit(True)
        return True

    def disconnect(self):
        """断开串口"""
        if self._worker:
            self._worker.stop()
            self._worker = None
        self._is_connected = False
        self._handshake = None
        self.connection_changed.emit(False)
    
    def send(self, data: str):
        """发送数据"""
        if self._worker:
            self._worker.send_data(data)
    
    def _on_data_received(self, data: UnifiedData):
        self.data_received.emit(data)
    
    def _on_handshake_received(self, handshake: HandshakeInfo):
        self._handshake = handshake
        self.handshake_received.emit(handshake)

    def _on_error(self, message: str):
        self.error_occurred.emit(message)
    
    def _on_connection_lost(self):
        self._is_connected = False
        self._handshake = None
        self.connection_changed.emit(False)
