import threading
import time
import re
from PyQt_Service.Database.db import db
from PyQt_Service.Log.log_manager import LogManager


class MonitoringCollector:
    def __init__(self, serial_manager):
        self.serial = serial_manager
        self.running = False

    # ========================================
    # 시작 / 중지
    # ========================================
    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self.collect_loop, daemon=True).start()
        LogManager.instance().log("📡 데이터 수집 스레드 시작됨")

    def stop(self):
        self.running = False
        LogManager.instance().log("⏹ 데이터 수집 스레드 중지됨")

    # ========================================
    # 메인 루프 (1분마다 실행)
    # ========================================
    def collect_loop(self):
        while self.running:

            # 0) 연결 체크
            if not self.serial.is_connected:
                LogManager.instance().log("❌ 수집 실패 – 시리얼 연결 안됨")
                time.sleep(60)
                continue

            # 1) $ue 명령 전송
            sent = self.serial.send("$ue")
            if not sent:
                LogManager.instance().log("⚠️ $ue 전송 실패 – 저장 안함")
                time.sleep(60)
                continue

            LogManager.instance().log("📤 $ue 명령 전송됨")

            # 아두이노 처리시간 약간 기다림
            time.sleep(0.3)

            # 2) 응답 여러 줄 수신
            lines = []
            for _ in range(30):
                line = self.serial.read_line()
                if line:
                    lines.append(line)

            if not lines:
                LogManager.instance().log("❌ 응답 없음 – 하드웨어 미응답")
                time.sleep(60)
                continue

            LogManager.instance().log(f"📥 응답 {len(lines)}줄 수신")

            # 3) 파싱
            parsed = self.parse_system_status(lines)

            if not parsed:
                LogManager.instance().log("❌ 파싱 실패 – 저장 안함")
                time.sleep(60)
                continue

            LogManager.instance().log(
                f"🔍 파싱결과 → Voltage:{parsed['v']}V  Current:{parsed['i']}A  Power:{parsed['p']}W"
            )

            # 4) DB 저장
            saved = self.save_to_db(parsed)

            if saved:
                LogManager.instance().log(
                    f"✅ DB 저장완료 → V:{parsed['v']}  I:{parsed['i']}  P:{parsed['p']}"
                )
            else:
                LogManager.instance().log("❌ DB 저장 실패")

            time.sleep(60)

    # ========================================
    # 파싱 (아두이노 $ue 출력 맞춤)
    # ========================================
    @staticmethod
    def parse_system_status(lines):
        """
        아두이노 printSystemStatus() 출력 예시:

        Voltage: 14.21 V
        Current: 0.123 A
        Max Current: 0.456 A   (무시)
        Power: 5.67 W
        ...
        """

        solar_v = None
        solar_i = None
        solar_p = None

        # float 추출 정규식
        num_re = re.compile(r"[-]?[0-9]*\.?[0-9]+")

        for line in lines:
            text = line.strip()

            # Voltage
            if "Voltage:" in text and solar_v is None:
                m = num_re.findall(text)
                if m:
                    solar_v = float(m[0])
                continue

            # Current (Max Current 제외!)
            if "Current:" in text and "Max" not in text and solar_i is None:
                m = num_re.findall(text)
                if m:
                    solar_i = float(m[0])
                continue

            # Power
            if "Power:" in text and solar_p is None:
                m = num_re.findall(text)
                if m:
                    solar_p = float(m[0])
                continue

        # 값 3개 다 있어야 성공
        if solar_v is None or solar_i is None or solar_p is None:
            return None

        return {"v": solar_v, "i": solar_i, "p": solar_p}

    # ========================================
    # DB 저장
    # ========================================
    def save_to_db(self, data):
        try:
            conn = db.conn
            cur = conn.cursor()
            sql = """
                INSERT INTO measurement (ts, solar_v, solar_i, solar_p)
                VALUES (NOW(), %s, %s, %s)
            """
            cur.execute(sql, (data['v'], data['i'], data['p']))
            conn.commit()
            return True

        except Exception as e:
            LogManager.instance().log(f"DB Error: {e}")
            return False
