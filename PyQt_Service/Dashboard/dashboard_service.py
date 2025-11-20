import time
import re

class DashboardService:
    def __init__(self, serial_instance=None):
        self.serial = serial_instance
        self.last_received_ts = 0  # 연결 상태 판단용

    # ============================================================
    # 안정적인 시리얼 송신 + 응답 수신 함수 (개선버전)
    # ============================================================
    def send_cmd(self, cmd):
        """
        Arduino에 명령 전달: $cmd e
        Arduino 응답을 최대 1초간 기다리고 개행(\n) 기준으로 수신
        """
        if self.serial is None:
            return None

        full_cmd = f"${cmd}e"

        try:
            # 🔥 기존 버퍼 정리
            self.serial.reset_input_buffer()
            self.serial.write(full_cmd.encode())
            self.serial.flush()
        except Exception as e:
            print("Serial Write Error:", e)
            return None

        # 🔥 Arduino 응답 수신 대기
        timeout = time.time() + 1.0  # 최대 1초 기다림
        buffer = ""

        while time.time() < timeout:
            if self.serial.in_waiting > 0:
                try:
                    buffer += self.serial.read(self.serial.in_waiting).decode(errors="ignore")
                except:
                    pass

                # Arduino println → \n 으로 끝남
                if buffer.endswith("\n") or buffer.endswith("\r\n"):
                    break

            time.sleep(0.01)

        # 수신이 있었으면 연결 유지 시간 갱신
        if buffer.strip():
            self.last_received_ts = time.time()

        return buffer

    # ============================================================
    # 1) Total Battery Voltage 읽기  ($r)
    # ============================================================
    def read_total_voltage(self):
        raw = self.send_cmd("r")
        if raw is None:
            return None

        # 예: "Voltage: 12.345V"
        match = re.search(r"Voltage:\s*([\d\.]+)V", raw)
        if match:
            try:
                return float(match.group(1))
            except:
                return None

        return None

    # ============================================================
    # 2) 태양광 Power 읽기 ($k)
    # ============================================================
    def read_solar_power(self):
        raw = self.send_cmd("k")
        if raw is None:
            return None

        # 예: "Power: 18.52 W"
        match = re.search(r"Power:\s*([\d\.]+)\s*W", raw)
        if match:
            try:
                return float(match.group(1))
            except:
                return None

        return None

    # ============================================================
    # 3) 전체 시스템 상태 읽기 ($u)
    # ============================================================
    def read_system_status(self):
        raw = self.send_cmd("u")
        if raw is None:
            return None

        status = {
            "pilot": None,
            "fan_commercial": None,
            "fan_battery": None,
            "halogen": None
        }

        # Pilot Lamp 상태
        m_pilot = re.search(r"Pilot Lamp.*: *(GREEN|RED|OFF)", raw)
        if m_pilot:
            status["pilot"] = m_pilot.group(1)

        # Commercial Fan 상태
        m_fc = re.search(r"Commercial Power:\s*(ON|OFF)", raw)
        if m_fc:
            status["fan_commercial"] = m_fc.group(1)

        # Battery Fan 상태
        m_fb = re.search(r"Battery Power:\s*(ON|OFF)", raw)
        if m_fb:
            status["fan_battery"] = m_fb.group(1)

        # Halogen Lamp 상태
        m_h = re.search(r"Halogen Lamp Status.*:\s*(ON|OFF)", raw)
        if m_h:
            status["halogen"] = m_h.group(1)

        return status

    # ============================================================
    # 연결 상태 판단
    # ============================================================
    def is_connected(self):
        return (time.time() - self.last_received_ts) < 3
