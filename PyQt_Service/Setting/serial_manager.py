import serial
import serial.tools.list_ports
import time

class SerialManager:
    def __init__(self):
        self.port = None
        self.is_connected = False

    # --------------------------------------------------------
    # 1) USB 포트 목록 가져오기 (장치 이름 포함)
    # --------------------------------------------------------
    def list_ports(self):
        """
        사용 가능한 COM 포트 + 장치 이름 반환
        예: [("COM3", "USB-SERIAL CH340"), ("COM4", "Arduino Uno")]
        """
        ports = serial.tools.list_ports.comports()
        result = []

        for p in ports:
            name = p.description  # ex) "USB-SERIAL CH340", "Arduino Uno"
            device = p.device     # ex) "COM3"
            result.append((device, name))

        return result

    # --------------------------------------------------------
    # 2) connect() 개선 — 장치 응답 테스트 포함
    # --------------------------------------------------------
    def connect(self, port_name: str):
        """
        포트 연결 + 아두이노 응답 검사 ($re 명령)
        """
        try:
            # 포트 열기
            self.port = serial.Serial(port_name, 115200, timeout=1)
            time.sleep(1)  # 포트 초기 안정화

            # 장치 확인용 명령 보내기
            self.port.write(b"$re")
            time.sleep(0.3)
            resp = self.port.readline().decode().strip()

            print(f"[Serial] Handshake response: '{resp}'")

            # 응답이 없으면 실패 처리
            if resp == "":
                raise Exception("No response from device")

            # 여기까지 왔으면 진짜 연결 성공
            self.is_connected = True
            return True

        except Exception as e:
            print("[Serial] Connection Error:", e)

            # 실패 시 포트 닫기
            try:
                if self.port and self.port.is_open:
                    self.port.close()
            except:
                pass

            self.is_connected = False
            return False

    # --------------------------------------------------------
    # 3) disconnect()
    # --------------------------------------------------------
    def disconnect(self):
        """포트 해제"""
        if self.port and self.port.is_open:
            self.port.close()
        self.is_connected = False

    # --------------------------------------------------------
    # 4) send()
    # --------------------------------------------------------
    def send(self, cmd: str):
        """명령 전송"""
        if not self.is_connected:
            print("[Serial] Not connected")
            return False

        packet = f"{cmd}".encode()
        print("[Serial Send]", packet)
        self.port.write(packet)
        return True
