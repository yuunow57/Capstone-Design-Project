# PyQt_Service/Monitoring/serial_manager.py

import serial
import threading
import time


class SerialManager:
    def __init__(self, port="COM3", baud=115200):
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            print(f"✅ Serial connected: {port}")
        except Exception as e:
            print(f"❌ Serial Connect Failed: {e}")
            self.ser = None

        self.running = True
        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

    # 단순 read loop
    def read_loop(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    if line:
                        print("📥 Serial:", line)
            except Exception as e:
                print("Serial Error:", e)

            time.sleep(0.05)
