from PyQt_Service.Log.log_manager import LogManager
import time


class CommandService:
    """
    Arduino 펌웨어(.ino)와 통신하기 위한 명령 서비스.
    아두이노는 '$' + (명령문자) + 'e' 형태로 명령을 받는다.
    """

    def __init__(self, serial_manager):
        self.serial = serial_manager

        # 명령 → 한국어 설명 매핑
        self.command_label = {
            "a": "파일럿 램프 OFF",
            "b": "파일럿 램프 GREEN",
            "c": "파일럿 램프 RED",
            "d": "상용 선풍기 ON",
            "e": "상용 선풍기 OFF",
            "f": "배터리 선풍기 ON",
            "g": "배터리 선풍기 OFF",
            "h": "할로겐 램프 ON",
            "i": "할로겐 램프 OFF",
            "j": "배터리 전압 읽기",
            "k": "VC_MON 데이터 읽기",
            "l": "VC_MON 데이터 리셋",
            "m": "VC_MON 자동 송신 시작",
            "n": "VC_MON 자동 송신 정지",
            "o": "1S 전압 읽기",
            "p": "2S 전압 읽기",
            "q": "3S 전압 읽기",
            "r": "총 전압 읽기",
            "s": "전압 보정값 출력",
            "t": "모든 전압 출력",
            "u": "시스템 상태 출력",
            "v": "태양광 데이터 리셋"
        }

    # ─────────────────────────────────────
    # 내부 송신 함수 + 아두이노 응답 읽기(Log 출력)
    # ─────────────────────────────────────
    def _send(self, char: str) -> bool:
        packet = f"${char}e"
        label = self.command_label.get(char, f"명령 {char}")

        ok = self.serial.send(packet)

        # 명령 전송 로그
        if ok:
            LogManager.instance().log(f"{label} → 전송됨")
        else:
            LogManager.instance().log(f"{label} → 실패 (포트 미연결)")
            return False

        # 0.15초 대기 (아두이노 반응 시간)
        time.sleep(0.15)

        # 아두이노 응답 읽기 (최대 2초)
        deadline = time.time() + 2.0
        response_lines = []
        while time.time() < deadline:
            line = self.serial.read_line()
            if not line:
                continue

            response_lines.append(line)

        # 로그 출력
        if response_lines:
            for line in response_lines:
                LogManager.instance().log(f"[응답] {line}")
        else:
            LogManager.instance().log(f"[응답 없음] ({label})")

        return True

    # ─────────────────────────────────────
    # 파일럿 램프
    # ─────────────────────────────────────
    def pilot_off(self) -> bool:
        return self._send("a")

    def pilot_green(self) -> bool:
        return self._send("b")

    def pilot_red(self) -> bool:
        return self._send("c")

    # ─────────────────────────────────────
    # 선풍기 — 상용(SMPS)
    # ─────────────────────────────────────
    def fan_commercial_on(self) -> bool:
        return self._send("d")

    def fan_commercial_off(self) -> bool:
        return self._send("e")

    # ─────────────────────────────────────
    # 선풍기 — 배터리 모듈
    # ─────────────────────────────────────
    def fan_battery_on(self) -> bool:
        return self._send("f")

    def fan_battery_off(self) -> bool:
        return self._send("g")

    # ─────────────────────────────────────
    # 할로겐 램프
    # ─────────────────────────────────────
    def halogen_on(self) -> bool:
        return self._send("h")

    def halogen_off(self) -> bool:
        return self._send("i")

    # ─────────────────────────────────────
    # 배터리/VC_MON 데이터 출력
    # ─────────────────────────────────────
    def print_battery_voltage(self) -> bool:
        return self._send("j")

    def print_vcmon_data(self) -> bool:
        return self._send("k")

    def reset_vcmon_data(self) -> bool:
        return self._send("l")

    def start_vcmon_auto(self) -> bool:
        return self._send("m")

    def stop_vcmon_auto(self) -> bool:
        return self._send("n")

    # ─────────────────────────────────────
    # 개별 전압
    # ─────────────────────────────────────
    def read_1s(self) -> bool:
        return self._send("o")

    def read_2s(self) -> bool:
        return self._send("p")

    def read_3s(self) -> bool:
        return self._send("q")

    def read_total(self) -> bool:
        return self._send("r")

    # ─────────────────────────────────────
    # 기타 시스템 정보
    # ─────────────────────────────────────
    def print_voltage_calibration(self) -> bool:
        return self._send("s")

    def print_all_voltages(self) -> bool:
        return self._send("t")

    def print_system_status(self) -> bool:
        return self._send("u")

    def reset_solar_data(self) -> bool:
        return self._send("v")
