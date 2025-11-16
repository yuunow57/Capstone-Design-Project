import threading
import time
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
                LogManager.instance().log("⚠️ 수집 실패 – 시리얼 연결 안됨")
                time.sleep(60)
                continue

            # 1) 명령 전송
            sent = self.serial.send("$ue")
            if not sent:
                LogManager.instance().log("⚠️ $ue 전송 실패 – 저장 안함")
                time.sleep(60)
                continue

            LogManager.instance().log("📤 $ue 명령 전송됨")

            time.sleep(0.3)

            # 2) 응답 여러 줄 수신
            lines = []
            for _ in range(20):
                try:
                    line = self.serial.read_line()
                except:
                    line = None
                if line:
                    lines.append(line)

            if not lines:
                LogManager.instance().log("❌ 응답 없음 – 하드웨어 미응답")
                time.sleep(60)
                continue

            LogManager.instance().log(f"📥 응답 수신: {len(lines)}줄")

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

            # 다음 주기
            time.sleep(60)

    # ========================================
    # 데이터 파싱
    # ========================================
    @staticmethod
    def parse_system_status(lines):
        v = i = p = None

        for line in lines:
            if "Voltage:" in line:
                v = MonitoringCollector.extract_number(line)
            elif "Current:" in line and "Max" not in line:
                i = MonitoringCollector.extract_number(line)
            elif "Power:" in line:
                p = MonitoringCollector.extract_number(line)

        if v is None or i is None or p is None:
            return None

        return {"v": v, "i": i, "p": p}

    @staticmethod
    def extract_number(text):
        try:
            num = "".join(c for c in text if (c.isdigit() or c == "."))
            return float(num)
        except:
            return None

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
