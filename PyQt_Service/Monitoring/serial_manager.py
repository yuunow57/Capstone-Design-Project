import serial
import threading
import time
from datetime import datetime
from PyQt_Service.Database.db import db

class SerialManager:
    def __init__(self, port="COM3", baud=115200):
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            print(f"✅ Serial connected: {port}")
            self.running = True
            self.thread = threading.Thread(target=self.read_loop)
            self.thread.start()
        except Exception as e:
            print(f"❌ Serial Connect Failed: {e}")
            self.ser = None
            self.running = False

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

    # 🔥 Serial read → DB insert loop
    def read_loop(self):
        conn = db.conn
        cursor = conn.cursor()

        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode().strip()

                    # VC_MON 패턴 데이터만 처리
                    if "VC_MON Data" in line:
                        parts = line.split(',')
                        # 형식: V:24.01V, I:0.30A, P:7.02W
                        v = float(parts[0].split(':')[1].replace('V', ''))
                        i = float(parts[1].split(':')[1].replace('A', ''))
                        p = float(parts[2].split(':')[1].replace('W', ''))

                        sql = """
                        INSERT INTO measurement (ts, solar_v, solar_i, solar_p)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(sql, (datetime.now(), v, i, p))
                        conn.commit()

                        print(f"📌 INSERT → V:{v} I:{i} P:{p}")

            except Exception as e:
                print("Serial Error:", e)

            time.sleep(0.05)  # CPU 과부하 방지
