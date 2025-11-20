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

    def __init__(self, ui, serial_manager, system_state):
        super().__init__()

        self.ui = ui
        self.serial = serial_manager
        self.system_state = system_state

        self.log = LogService()
        self.repo = MonitoringRepository()

        # ─────────────────────────────────────────────
        # 📌 UI Label 참조
        # ─────────────────────────────────────────────
        self.label_time   = self.ui.findChild(QtWidgets.QLabel, "label_3")
        self.label_batt   = self.ui.findChild(QtWidgets.QLabel, "battery_status_label")
        self.label_solar  = self.ui.findChild(QtWidgets.QLabel, "solar_power_label")
        self.label_status = self.ui.findChild(QtWidgets.QLabel, "label_5")
        self.graph_widget = self.ui.findChild(QtWidgets.QWidget, "widget_graph_area")

        # ⭐ 추가됨: 시스템 상태 UI 라벨 4개
        self.label_pilot  = self.ui.findChild(QtWidgets.QLabel, "label_8")
        self.label_commercial_fan = self.ui.findChild(QtWidgets.QLabel, "label_9")
        self.label_battery_fan = self.ui.findChild(QtWidgets.QLabel, "label_10")
        self.label_halogen = self.ui.findChild(QtWidgets.QLabel, "label_11")

        # ─────────────────────────────────────────────
        # 📌 Matplotlib 그래프 설정
        # ─────────────────────────────────────────────
        self.fig = Figure(figsize=(4, 2))
        self.canvas = FigureCanvas(self.fig)

        layout = QtWidgets.QVBoxLayout(self.graph_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        # 30분 버퍼
        self.time_buffer = []
        self.voltage_buffer = []
        self.buffer_limit = 30

        # ─────────────────────────────────────────────
        # 📌 1초 UI 업데이트 타이머
        # ─────────────────────────────────────────────
        self.timer_ui = QtCore.QTimer()
        self.timer_ui.timeout.connect(self.update_ui)
        self.timer_ui.start(1000)

        # ─────────────────────────────────────────────
        # 📌 1분 간격 총전압 수집 스레드
        # ─────────────────────────────────────────────
        self.thread = threading.Thread(target=self.collect_voltage, daemon=True)
        self.thread.start()

    # ===============================================================
    # 1분마다 총전압 읽기
    # ===============================================================
    def collect_voltage(self):
        while True:
            voltage = self.read_total_voltage()
            now = datetime.now().strftime("%H:%M")

            if voltage is not None:
                self.time_buffer.append(now)
                self.voltage_buffer.append(voltage)
            else:
                LogManager.instance().log("⚠️ 총전압 갱신 실패 (None)")

            if len(self.voltage_buffer) > self.buffer_limit:
                self.time_buffer.pop(0)
                self.voltage_buffer.pop(0)

            self.update_graph()
            time.sleep(60)

    # ===============================================================
    # '$re' → 총전압 읽기 (자동 데이터 섞임 방지)
    # ===============================================================
    def read_total_voltage(self) -> float:
        try:
            if not (self.serial.is_connected and self.serial.port):
                return None

            # 🔥 명령 보내기 전 버퍼 정리
            self.serial.port.reset_input_buffer()

            # 🔥 명령 전송
            self.serial.port.write(b"$re")
            self.serial.port.flush()

            deadline = time.time() + 1.0
            line = ""

            # 🔥 "Voltage:" 포함될 때까지 여러 줄 읽기
            while time.time() < deadline:
                raw = self.serial.port.readline().decode(errors="ignore").strip()

                if not raw:
                    continue

                if "Voltage:" in raw:
                    line = raw
                    break

            if not line:
                self.log.add("⚠️ 총전압 응답 없음")
                return None

            # "Voltage: 12.34V" 파싱
            import re
            match = re.search(r"Voltage:\s*([0-9.]+)", line)
            if match:
                voltage = float(match.group(1))
                self.log.add(f"총전압 수신 성공: {voltage} V")
                return voltage

            self.log.add(f"⚠️ 전압 파싱 실패: {line}")

        except Exception as e:
            self.log.add(f"⚠️ read_total_voltage 오류: {e}")

        return None

    # ===============================================================
    # DB에서 solar_p 최신 값 가져오기
    # ===============================================================
    def get_latest_solar_power(self) -> float:
        row = self.repo.get_latest_measurement()
        if row is None:
            return 0.0

        try:
            return float(row["solar_p"])
        except:
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
    # UI 업데이트 (1초)
    # ===============================================================
    def update_ui(self):

        # ─────────────────────────────────────────────
        # (1) 현재 시각 — 14pt
        # ─────────────────────────────────────────────
        now = datetime.now().strftime("%H:%M:%S")
        if self.label_time:
            self.label_time.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>현재 시각 : </span>"
                f"<span style='font-size:14pt; color:#00ac00;'>{now}</span>"
                f"</p></body></html>"
            )

        # ─────────────────────────────────────────────
        # (2) 이차전지 모듈 상태 — 14pt
        # ─────────────────────────────────────────────
        if self.voltage_buffer:
            latest_voltage = self.voltage_buffer[-1]
            batt_text = f"{latest_voltage:.2f} V"
        else:
            latest_voltage = 0.0
            batt_text = "---- V"

        if self.label_batt:
            self.label_batt.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>이차전지 모듈 상태 : </span>"
                f"<span style='font-size:14pt; color:#00ac00;'>{batt_text}</span>"
                f"</p></body></html>"
            )

        # ─────────────────────────────────────────────
        # (3) 태양광 발전 데이터 — 14pt
        # ─────────────────────────────────────────────
        solar_p = self.get_latest_solar_power()
        if self.label_solar:
            self.label_solar.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>태양광 발전 데이터 : </span>"
                f"<span style='font-size:14pt; color:#930b0d;'>{solar_p:.2f} W</span>"
                f"</p></body></html>"
            )

        # ─────────────────────────────────────────────
        # (4) 연결 상태 — 14pt
        # ─────────────────────────────────────────────
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

        # ===============================================================
        # ⭐ 아래는 기존 시스템 상태(파일럿/팬/할로겐) — 그대로 유지
        # ===============================================================

        # 파일럿 램프
        if hasattr(self, "label_pilot"):
            pilot_state = self.system_state.get("pilot", "RED")  # 기본 RED

            if pilot_state == "RED":
                color = "#930b0d"
            elif pilot_state == "GREEN":
                color = "#00ac00"
            else:  # "OFF"
                color = "#666666"

            self.label_pilot.setText(
                f"<html><body><p align='center'>"
                f"<span style='font-size:14pt;'>🚦 파일럿 램프 : </span>"
                f"<span style='font-size:14pt; color:{color};'>{pilot_state}</span>"
                f"</p></body></html>"
            )

        # 상용 선풍기
        if hasattr(self, "label_commercial_fan"):
            on = self.system_state.get("fan_commercial", False)
            color = "#00ac00" if on else "#930b0d"
            text = "ON" if on else "OFF"

            self.label_commercial_fan.setText(
                f"<html><body><p align='center'>"
                f"<span style='font-size:14pt;'>🌪️ 상용 선풍기 : </span>"
                f"<span style='font-size:14pt; color:{color};'>{text}</span>"
                f"</p></body></html>"
            )

        # 배터리 선풍기
        if hasattr(self, "label_battery_fan"):
            on = self.system_state.get("fan_battery", False)
            color = "#00ac00" if on else "#930b0d"
            text = "ON" if on else "OFF"

            self.label_battery_fan.setText(
                f"<html><body><p align='center'>"
                f"<span style='font-size:14pt;'>🔋 배터리 선풍기 : </span>"
                f"<span style='font-size:14pt; color:{color};'>{text}</span>"
                f"</p></body></html>"
            )

        # 할로겐 램프
        if hasattr(self, "label_halogen"):
            on = self.system_state.get("halogen", False)
            color = "#00ac00" if on else "#930b0d"
            text = "ON" if on else "OFF"

            self.label_halogen.setText(
                f"<html><body><p align='center'>"
                f"<span style='font-size:14pt;'>💡 할로겐 램프 : </span>"
                f"<span style='font-size:14pt; color:{color};'>{text}</span>"
                f"</p></body></html>"
            )
