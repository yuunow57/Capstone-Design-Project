import threading
import time
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt_Service.Log.log_service import LogService
from PyQt_Service.Log.log_manager import LogManager


class DashboardController(QtCore.QObject):

    def __init__(self, ui, serial_manager, system_state):
        super().__init__()

        self.ui = ui
        self.serial = serial_manager
        self.system_state = system_state

        self.log = LogService()

        # ─────────────────────────────
        # UI Label 가져오기
        # ─────────────────────────────
        self.label_time = self.ui.findChild(QtWidgets.QLabel, "label_3")
        self.label_batt = self.ui.findChild(QtWidgets.QLabel, "battery_status_label")
        self.label_solar = self.ui.findChild(QtWidgets.QLabel, "solar_power_label")
        self.label_status = self.ui.findChild(QtWidgets.QLabel, "label_5")
        self.graph_widget = self.ui.findChild(QtWidgets.QWidget, "widget_graph_area")

        self.label_pilot = self.ui.findChild(QtWidgets.QLabel, "label_8")
        self.label_commercial_fan = self.ui.findChild(QtWidgets.QLabel, "label_9")
        self.label_battery_fan = self.ui.findChild(QtWidgets.QLabel, "label_10")
        self.label_halogen = self.ui.findChild(QtWidgets.QLabel, "label_11")

        # ─────────────────────────────
        # 그래프 준비
        # ─────────────────────────────
        self.fig = Figure(figsize=(4, 2))
        self.canvas = FigureCanvas(self.fig)
        layout = QtWidgets.QVBoxLayout(self.graph_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.time_buffer = []
        self.voltage_buffer = []
        self.buffer_limit = 30

        # UI 업데이트 타이머
        self.timer_ui = QtCore.QTimer()
        self.timer_ui.timeout.connect(self.update_ui)
        self.timer_ui.start(1000)

        # 1분마다 총전압 읽기 스레드
        self.thread = threading.Thread(target=self.collect_voltage, daemon=True)
        self.thread.start()

    # ===============================================================
    # 1분마다 총전압 읽기 (시리얼 하드웨어)
    # ===============================================================
    def collect_voltage(self):
        while True:
            voltage = self.read_total_voltage()
            now = datetime.now().strftime("%H:%M")

            if voltage is not None:
                self.time_buffer.append(now)
                self.voltage_buffer.append(voltage)

                # 대시보드에 표시할 최신값 저장
                self.system_state["latest_voltage"] = voltage

            else:
                LogManager.instance().log("⚠️ 총전압 갱신 실패")

            # 버퍼 제한
            if len(self.voltage_buffer) > self.buffer_limit:
                self.time_buffer.pop(0)
                self.voltage_buffer.pop(0)

            self.update_graph()
            time.sleep(60)

    # ===============================================================
    # '$re' → 총전압 읽기
    # ===============================================================
    def read_total_voltage(self) -> float:
        try:
            if not (self.serial.is_connected and self.serial.port):
                return None

            self.serial.port.reset_input_buffer()
            self.serial.port.write(b"$re")
            self.serial.port.flush()

            deadline = time.time() + 1.0
            line = ""

            while time.time() < deadline:
                raw = self.serial.port.readline().decode(errors="ignore").strip()
                if "Voltage:" in raw:
                    line = raw
                    break

            if not line:
                self.log.add("⚠️ 총전압 응답 없음")
                return None

            import re
            match = re.search(r"Voltage:\s*([0-9.]+)", line)
            if match:
                voltage = float(match.group(1))
                return voltage

        except Exception as e:
            self.log.add(f"⚠️ read_total_voltage 오류: {e}")

        return None

    # ===============================================================
    # 그래프 업데이트
    # ===============================================================
    def update_graph(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if self.voltage_buffer:
            ax.plot(
                self.time_buffer,
                self.voltage_buffer,
                color="#4C934C",
                linewidth=1.8,
            )

        ax.grid(True)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=7)

        self.canvas.draw_idle()

    # ===============================================================
    # UI 업데이트 (1초)
    # ===============================================================
    def update_ui(self):

        # (1) 현재 시각
        now = datetime.now().strftime("%H:%M:%S")
        if self.label_time:
            self.label_time.setText(
                f"<html><body><p>"
                f"<span style='font-size:14pt;'>현재 시각 : </span>"
                f"<span style='font-size:14pt; color:#00ac00;'>{now}</span>"
                f"</p></body></html>"
            )

        # (2) 이차전지 모듈 상태 (총전압)
        latest_voltage = self.system_state.get("latest_voltage", 0.0)
        batt_text = f"{latest_voltage:.2f} V" if latest_voltage else "---- V"

        self.label_batt.setText(
            f"<html><body><p>"
            f"<span style='font-size:14pt;'>이차전지 모듈 상태 : </span>"
            f"<span style='font-size:14pt; color:#00ac00;'>{batt_text}</span>"
            f"</p></body></html>"
        )

        # (3) 태양광 발전량 — MonitoringController에서 전달된 난수 power
        solar_p = self.system_state.get("last_power", 0.0)

        self.label_solar.setText(
            f"<html><body><p>"
            f"<span style='font-size:14pt;'>태양광 발전 데이터 : </span>"
            f"<span style='font-size:14pt; color:#930b0d;'>{solar_p:.2f} W</span>"
            f"</p></body></html>"
        )

        # (4) 연결 상태
        if self.serial.is_connected:
            status_color = "#0014a9"
            status_text = "정상"
        else:
            status_color = "#930b0d"
            status_text = "연결해제"

        self.label_status.setText(
            f"<html><body><p>"
            f"<span style='font-size:14pt;'>연결 상태 : </span>"
            f"<span style='font-size:14pt; color:{status_color};'>{status_text}</span>"
            f"</p></body></html>"
        )

        # ─────────────────────────────
        # 시스템 상태 표시 (pilot, fan, halogen)
        # ─────────────────────────────

        # 파일럿 램프
        pilot_state = self.system_state.get("pilot", "RED")
        color = "#00ac00" if pilot_state == "GREEN" else "#930b0d"
        self.label_pilot.setText(
            f"<html><body><p align='center'>"
            f"<span style='font-size:14pt;'>🚦 파일럿 램프 : </span>"
            f"<span style='font-size:14pt; color:{color};'>{pilot_state}</span>"
            f"</p></body></html>"
        )

        # 상용 선풍기
        fc = self.system_state.get("fan_commercial", False)
        color = "#00ac00" if fc else "#930b0d"
        text = "ON" if fc else "OFF"
        self.label_commercial_fan.setText(
            f"<html><body><p align='center'>"
            f"<span style='font-size:14pt;'>🌪️ 상용 선풍기 : </span>"
            f"<span style='font-size:14pt; color:{color};'>{text}</span>"
            f"</p></body></html>"
        )

        # 배터리 선풍기
        fb = self.system_state.get("fan_battery", False)
        color = "#00ac00" if fb else "#930b0d"
        text = "ON" if fb else "OFF"
        self.label_battery_fan.setText(
            f"<html><body><p align='center'>"
            f"<span style='font-size:14pt;'>🔋 배터리 선풍기 : </span>"
            f"<span style='font-size:14pt; color:{color};'>{text}</span>"
            f"</p></body></html>"
        )

        # 할로겐 램프
        halogen = self.system_state.get("halogen", False)
        color = "#00ac00" if halogen else "#930b0d"
        text = "ON" if halogen else "OFF"
        self.label_halogen.setText(
            f"<html><body><p align='center'>"
            f"<span style='font-size:14pt;'>💡 할로겐 램프 : </span>"
            f"<span style='font-size:14pt; color:{color};'>{text}</span>"
            f"</p></body></html>"
        )
