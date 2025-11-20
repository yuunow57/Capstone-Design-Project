import serial
import serial.tools.list_ports
import time


class SerialManager:
    def __init__(self):
        self.port = None            # pyserial 객체
        self.is_connected = False   # 연결 상태 Boolean

    # ========================================
    # 사용 가능한 포트 목록 가져오기
    # ========================================
    def list_ports(self):
        """Windows / macOS 포트 목록 반환"""
        return list(serial.tools.list_ports.comports())

    # ========================================
    # 포트 연결
    # ========================================
    def connect(self, port_name):
        """포트 연결 시도"""
        try:
            self.port = serial.Serial(
                port_name,
                115200,
                timeout=1,
                dsrdtr=False,
                rtscts=False
            )
            time.sleep(0.2)

            self.is_connected = True
            return True

        except Exception as e:
            print("[Serial] Connection Error:", e)
            self.port = None
            self.is_connected = False
            return False

    # ========================================
    # 포트 해제
    # ========================================
    def disconnect(self):
        if self.port and self.port.is_open:
            self.port.close()
        self.port = None
        self.is_connected = False

    # ========================================
    # 텍스트 명령 전송 (기존 방식)
    # ========================================
    def send(self, cmd: str):
        """'$ue' → '$ue\\n' 자동 변환 후 전송"""
        if not self.is_connected or self.port is None:
            print("[Serial] Not connected")
            return False

        try:
            packet = f"{cmd}\n".encode()
            self.port.write(packet)
            self.port.flush()
            return True

        except Exception as e:
            print("[Serial] Send Error:", e)
            return False

    # ========================================
    # 한 줄 읽기
    # ========================================
    def read_line(self):
        """시리얼의 한 줄 읽어 UTF-8 문자열로 반환 (읽을 게 없으면 '')"""
        try:
            if self.port and self.port.is_open:
                line = self.port.readline().decode(errors="ignore").strip()
                return line
        except:
            return ""
        return ""

    # ========================================
    # ⭐ DashboardController 호환을 위한 추가 메서드
    # ========================================

    def reset_input_buffer(self):
        """Dashboard에서 사용하는 버퍼 삭제 함수"""
        if self.port and self.port.is_open:
            try:
                self.port.reset_input_buffer()
            except:
                pass

    def write(self, data: bytes):
        """Dashboard에서 raw bytes 직접 전송하는 write 함수"""
        if self.port and self.port.is_open:
            try:
                self.port.write(data)
            except:
                pass

    def flush(self):
        """Dashboard에서 사용하는 flush 함수"""
        if self.port and self.port.is_open:
            try:
                self.port.flush()
            except:
                pass
