import time
import re

class DashboardService:
    def __init__(self, serial_instance=None):
        self.serial = serial_instance
        self.last_received_ts = 0  # 연결 상태 판단용

    # =====================
    # 기본 시리얼 송신 함수
    # =====================
    def send_cmd(self, cmd):
        """
        cmd: 'r', 'k', 'u' 같은 명령
        실제 보내는 형식은 $r + 'e' 형태
        """
        if self.serial is None:
            return None

        full_cmd = f"${cmd}e"
        try:
            self.serial.write(full_cmd.encode())
            self.serial.flush()
        except:
            return None

        time.sleep(0.1)
        try:
            data = self.serial.read_all().decode(errors="ignore")
            if data.strip():
                self.last_received_ts = time.time()
            return data
        except:
            return None

    # =====================
    # Total Voltage 값 파싱 ($r)
    # =====================
    def read_total_voltage(self):
        raw = self.send_cmd("r")
        if raw is None:
            return None

        # 예: "A3 (Total) - ADC: 678 | Voltage: 12.345V"
        match = re.search(r"Voltage:\s*([\d\.]+)V", raw)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        return None

    # =====================
    # 태양광 발전 Power 값 ($k)
    # =====================
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

    # =====================
    # 전체 시스템 상태 ($u)
    # =====================
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

        # Pilot Lamp
        m_pilot = re.search(r"Pilot Lamp.*: *(GREEN|RED|OFF)", raw)
        if m_pilot:
            status["pilot"] = m_pilot.group(1)

        # Commercial Fan
        m_fc = re.search(r"Commercial Power:\s*(ON|OFF)", raw)
        if m_fc:
            status["fan_commercial"] = m_fc.group(1)

        # Battery Fan
        m_fb = re.search(r"Battery Power:\s*(ON|OFF)", raw)
        if m_fb:
            status["fan_battery"] = m_fb.group(1)

        # Halogen Lamp
        m_h = re.search(r"Halogen Lamp Status.*: *(ON|OFF)", raw)
        if m_h:
            status["halogen"] = m_h.group(1)

        return status

    # =====================
    # 연결 상태 체크
    # =====================
    def is_connected(self):
        if time.time() - self.last_received_ts < 3:
            return True
        return False
