# PyQt_Service/Dashboard/dashboard_controller.py

import threading
import time
from datetime import datetime

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt_Service.Monitoring.monitoring_repository import MonitoringRepository
from PyQt_Service.Log.log_service import LogService

class DashboardController(QtCore.QObject):
    """
    대시보드 페이지 컨트롤러

    - 이차전지 모듈 Total 전압: 1분 주기 측정, 30개 버퍼 (약 30분)
    - 현재 시각: 1초마다 갱신
    - 태양광 발전 데이터(solar_p): measurement 테이블 마지막 행의 solar_p
    - 연결 상태: SerialManager.is_connected
    """

    def __init__(self, ui, serial_manager, system_state):
        super().__init__()

        self.ui = ui
        self.serial = serial_manager        # SettingController.serial (SerialManager)
        self.system_state = system_state    # 현재 안 쓰지만 구조 유지

        self.log = LogService()

        self.repo = MonitoringRepository()

        # ─────────────────────────────────────────────
        # 📌 UI 위젯 참조
        # ─────────────────────────────────────────────
        self.label_time   = self.ui.findChild(QtWidgets.QLabel, "label_3")
        self.label_batt   = self.ui.findChild(QtWidgets.QLabel, "battery_status_label")
        self.label_solar  = self.ui.findChild(QtWidgets.QLabel, "solar_power_label")
        self.label_status = self.ui.findChild(QtWidgets.QLabel, "label_5")
        self.graph_widget = self.ui.findChild(QtWidgets.QWidget, "widget_graph_area")

        # ─────────────────────────────────────────────
        # 📌 Matplotlib 그래프 설정
        # ─────────────────────────────────────────────
        self.fig = Figure(figsize=(4, 3))
        self.canvas = FigureCanvas(self.fig)

        layout = QtWidgets.QVBoxLayout(self.graph_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        # 버퍼: 1분 간격 측정 30개 → 약 30분
        self.time_buffer = []
        self.voltage_buffer = []
        self.buffer_limit = 30

        # ─────────────────────────────────────────────
        # 📌 1초마다 UI 업데이트
        # ─────────────────────────────────────────────
        self.timer_ui = QtCore.QTimer()
        self.timer_ui.timeout.connect(self.update_ui)
        self.timer_ui.start(1000)  # 1초

        # ─────────────────────────────────────────────
        # 📌 1분마다 총전압 읽기 스레드 시작
        # ─────────────────────────────────────────────
        self.thread = threading.Thread(target=self.collect_voltage, daemon=True)
        self.thread.start()
        

    # ===============================================================
    # 1분마다 총전압 읽기 ($re)
    # ===============================================================
    def collect_voltage(self):
        while True:
            voltage = self.read_total_voltage()
            now = datetime.now().strftime("%H:%M")

            self.time_buffer.append(now)
            self.voltage_buffer.append(voltage)

            if len(self.voltage_buffer) > self.buffer_limit:
                self.time_buffer.pop(0)
                self.voltage_buffer.pop(0)

            self.update_graph()

            time.sleep(60)  # 1분마다

    # ===============================================================
    # 총전압 읽기 ($re 명령)
    # ===============================================================
    def read_total_voltage(self) -> float:
        """
        아두이노에서 '$re' 명령으로 Total 전압을 읽음.
        실패 시 테스트용 랜덤값 반환.
        """
        try:
            # SerialManager 구조:
            #   self.port: serial.Serial 객체
            #   self.is_connected: bool
            if self.serial.is_connected and self.serial.port:
                # '$re' + 'e' 형식으로 맞춰 줄 수도 있음
                # 아두이노 쪽 프로토콜에 맞게 필요하면 수정
                self.serial.port.write(b"$re")
                line = self.serial.port.readline().decode().strip()

                # 숫자와 '.'만 추출
                value = "".join(c for c in line if (c.isdigit() or c == "."))
                if value:
                    return float(value)
        except Exception as e:
            print("⚠️ read_total_voltage() ERROR:", e)

        # 하드웨어 연결 안 되었을 때 테스트 값
        import random
        return round(random.uniform(11.0, 14.0), 2)

    # ===============================================================
    # 태양광발전 최신값(solar_p) 가져오기
    # ===============================================================
    def get_latest_solar_power(self) -> float:
        """
        measurement 테이블에서 가장 마지막 행의 solar_p 값 반환
        """
        row = self.repo.get_latest_measurement()
        if row is None:
            return 0.0

        try:
            return float(row["solar_p"])
            
        except Exception as e:
            print("⚠️ get_latest_solar_power() 변환 오류:", e)
            return 0.0

    # ===============================================================
    # 그래프 업데이트
    # ===============================================================
    def update_graph(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if self.voltage_buffer:
            ax.plot(self.time_buffer, self.voltage_buffer,
                    color="#4C934C", linewidth=1.8)

        ax.set_ylabel("Battery Total Voltage (V)")
        ax.set_xlabel("Time (1min interval)")
        ax.grid(True)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        

        self.canvas.draw_idle()

    # ===============================================================
    # UI 업데이트 (매 1초)
    # ===============================================================
    def update_ui(self):
        # 기존 UI 업데이트 코드…

        # ─────────────────────────────────────
        # 시스템 상태 업데이트
        # ─────────────────────────────────────

        # 파일럿 램프
        pilot_green = self.system_state["pilot_green"]
        pilot_red = self.system_state["pilot_red"]

        # text_pilot = ""
        # if pilot_green:
        #     text_pilot = "파일럿램프: <b style='color:green'>GREEN ON</b>"
        # elif pilot_red:
        #     text_pilot = "파일럿램프: <b style='color:red'>RED ON</b>"
        # else:
        #     text_pilot = "파일럿램프: OFF"

        # self.ui.label_pilot.setText(text_pilot)

        # # 상용 선풍기
        # if self.system_state["fan_commercial"]:
        #     self.ui.label_fan_commercial.setText("상용 선풍기: <b style='color:green'>ON</b>")
        # else:
        #     self.ui.label_fan_commercial.setText("상용 선풍기: OFF")

        # # 배터리 선풍기
        # if self.system_state["fan_battery"]:
        #     self.ui.label_fan_battery.setText("배터리 선풍기: <b style='color:green'>ON</b>")
        # else:
        #     self.ui.label_fan_battery.setText("배터리 선풍기: OFF")

        # # 할로겐
        # if self.system_state["halogen"]:
        #     self.ui.label_halogen.setText("할로겐 램프: <b style='color:green'>ON</b>")
        # else:
        #     self.ui.label_halogen.setText("할로겐 램프: OFF")
