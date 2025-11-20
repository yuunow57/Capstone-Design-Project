# PyQt_Service/Monitoring/monitoring_controller.py

import random
import time
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

class MonitoringController(QtCore.QObject):
    def __init__(self, ui, system_state):
        super().__init__()
        self.ui = ui
        self.system_state = system_state

        # -------------------------------
        # 그래프 데이터 버퍼
        # -------------------------------
        self.times = []       # 시간
        self.voltages = []    # 전압
        self.currents = []    # 전류
        self.powers = []      # 전력
        self.energy = 0       # 누적 전력(Wh 단위)
        self.energy_list = [] # 그래프용

        # -------------------------------
        # Matplotlib 그래프 4개 생성
        # -------------------------------
        self.fig_voltage = Figure(figsize=(4, 3))
        self.fig_current = Figure(figsize=(4, 3))
        self.fig_power = Figure(figsize=(4, 3))
        self.fig_energy = Figure(figsize=(4, 3))

        self.canvas_voltage = FigureCanvas(self.fig_voltage)
        self.canvas_current = FigureCanvas(self.fig_current)
        self.canvas_power = FigureCanvas(self.fig_power)
        self.canvas_energy = FigureCanvas(self.fig_energy)

        self._setup_canvas()

        # -------------------------------
        # 30초마다 난수 생성 타이머
        # -------------------------------
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.generate_random_data)
        self.timer.start(30000)  # 30초

        # 첫 데이터 생성
        self.generate_random_data()

    # ---------------------------------------------------------
    # UI Frame에 Canvas 집어넣기
    # ---------------------------------------------------------
    def _setup_canvas(self):
        from PyQt5.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self.ui.frame)
        layout.addWidget(self.canvas_voltage)

        layout = QVBoxLayout(self.ui.frame_3)
        layout.addWidget(self.canvas_current)

        layout = QVBoxLayout(self.ui.frame_2)
        layout.addWidget(self.canvas_power)

        layout = QVBoxLayout(self.ui.frame_4)
        layout.addWidget(self.canvas_energy)

    # ---------------------------------------------------------
    # 할로겐 상태 기반 난수 생성
    # ---------------------------------------------------------
    def generate_random_data(self):
        halogen_on = self.system_state.get("halogen", False)

        if halogen_on:
            voltage = random.uniform(17.0, 22.0)
            current = random.uniform(0.06, 0.15)
        else:
            voltage = random.uniform(0.0, 2.0)
            current = random.uniform(0, 0.02)

        power = voltage * current

        # 누적 전력(Wh) 계산: 30초 = 0.00833시간
        self.energy += power * (30 / 3600)
        self.energy_list.append(self.energy)

        # 시계열 데이터 저장
        current_time = time.strftime("%H:%M:%S")
        self.times.append(current_time)
        self.voltages.append(voltage)
        self.currents.append(current)
        self.powers.append(power)
        self.system_state["last_power"] = power

        # 리스트 길이 제한(예: 최근 200개)
        MAX_LEN = 200
        if len(self.times) > MAX_LEN:
            self.times.pop(0)
            self.voltages.pop(0)
            self.currents.pop(0)
            self.powers.pop(0)
            self.energy_list.pop(0)

        # 그래프 업데이트
        self.update_graphs()

    # ---------------------------------------------------------
    # 그래프 4개 업데이트
    # ---------------------------------------------------------
    def update_graphs(self):
        # 전압
        self.fig_voltage.clear()
        ax = self.fig_voltage.add_subplot(111)
        ax.plot(self.times, self.voltages, color="#930B0D")
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(axis="x", rotation=0)   # ⭐ X축 세로 회전
        self.canvas_voltage.draw()

        # 전류
        self.fig_current.clear()
        ax = self.fig_current.add_subplot(111)
        ax.plot(self.times, self.currents, color="#0C6AA4")
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(axis="x", rotation=0)   # ⭐ X축 세로 회전
        self.canvas_current.draw()

        # 전력
        self.fig_power.clear()
        ax = self.fig_power.add_subplot(111)
        ax.plot(self.times, self.powers, color="#4C934C")
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(axis="x", rotation=0)   # ⭐ X축 세로 회전
        self.canvas_power.draw()

        # 누적 전력량
        self.fig_energy.clear()
        ax = self.fig_energy.add_subplot(111)
        ax.plot(self.times, self.energy_list, color="#740399")
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(axis="x", rotation=0)   # ⭐ X축 세로 회전
        self.canvas_energy.draw()