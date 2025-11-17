# PyQt_Service/Dashboard/dashboard_controller.py

import threading
import time
from datetime import datetime

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt_Service.Monitoring.monitoring_repository import MonitoringRepository
from PyQt_Service.Log.log_service import LogService
from PyQt_Service.Log.log_manager import LogManager

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
        self.fig = Figure(figsize=(4, 2))
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

            if voltage is not None:
                self.time_buffer.append(now)
                self.voltage_buffer.append(voltage)
            else:
                # 실패 시 그래프에 공백을 넣지 않음
                LogManager.instance().log("⚠️ 총전압 갱신 실패 (None)")

            # 버퍼 유지
            if len(self.voltage_buffer) > self.buffer_limit:
                self.time_buffer.pop(0)
                self.voltage_buffer.pop(0)

            self.update_graph()
            time.sleep(60)

    # ===============================================================
    # 총전압 읽기 ($re 명령)
    # ===============================================================
    def read_total_voltage(self) -> float:
        """
        아두이노 '$re' 명령 응답:
        예) "A3 (Total) - ADC: 1234 | Voltage: 13.456V"
        여기서 Voltage 뒤 숫자만 파싱해 float로 반환
        """
        try:
            if self.serial.is_connected and self.serial.port:

                # 1) 명령 전송
                self.serial.port.write(b"$re\n")
                time.sleep(0.1)

                # 2) 응답 한 줄 읽기
                line = self.serial.port.readline().decode(errors="ignore").strip()

                if not line:
                    self.log.add("⚠️ 총전압 응답 없음")
                    return None

                # 3) "Voltage:" 포함된 부분만 찾기
                if "Voltage" not in line:
                    self.log.add(f"⚠️ 예상치 못한 응답: {line}")
                    return None

                # 4) 숫자만 추출
                # ex) "A3 (Total) - ADC: 1234 | Voltage: 13.456V"
                # → "13.456"
                import re
                match = re.search(r"Voltage:\s*([0-9\.]+)", line)
                if match:
                    voltage = float(match.group(1))
                    self.log.add(f"총전압 수신 성공: {voltage} V")
                    return voltage

                self.log.add(f"⚠️ 전압 파싱 실패: {line}")
                return None

        except Exception as e:
            self.log.add(f"⚠️ read_total_voltage() 오류: {e}")

        return None

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

        ax.grid(True)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=7)
        

        self.canvas.draw_idle()

    # ===============================================================
    # UI 업데이트 (매 1초)
    # ===============================================================
    def update_ui(self):

        # ===============================================================
        # 1) 현재 시각
        # ===============================================================
        now = datetime.now().strftime("%H:%M:%S")
        if self.label_time:
            self.label_time.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>현재 시각 : </span>"
                f"<span style='font-size:14pt; color:#00ac00;'>{now}</span>"
                f"</p></body></html>"
            )

        # ===============================================================
        # 2) 이차전지 모듈 상태
        # ===============================================================
        if self.voltage_buffer:
            latest_voltage = self.voltage_buffer[-1]
            batt_text = f"{latest_voltage:.2f} V"
        else:
            batt_text = "---- V"

        if self.label_batt:
            self.label_batt.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>이차전지 모듈 상태 : </span>"
                f"<span style='font-size:14pt; color:#00ac00;'>{batt_text}</span>"
                f"</p></body></html>"
            )

        # ===============================================================
        # 3) 태양광 발전 데이터
        # ===============================================================
        try:
            solar_p = self.get_latest_solar_power()
            solar_text = f"{solar_p:.2f} W"
        except:
            solar_text = "0.00 W"

        if self.label_solar:
            self.label_solar.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>태양광 발전 데이터 : </span>"
                f"<span style='font-size:14pt; color:#930b0d;'>{solar_text}</span>"
                f"</p></body></html>"
            )

        # ===============================================================
        # 4) 연결 상태
        # ===============================================================
        if self.serial.is_connected:
            status_color = "#0014a9"
            status_text = "정상"
        else:
            status_color = "#930b0d"
            status_text = "연결해제"

        if self.label_status:
            self.label_status.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>연결 상태 : </span>"
                f"<span style='font-size:14pt; color:{status_color};'>{status_text}</span>"
                f"</p></body></html>"
            )
