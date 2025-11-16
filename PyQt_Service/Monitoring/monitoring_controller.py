import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt_Service.Monitoring.monitoring_service import MonitoringService
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt_Service.Log.log_manager import LogManager
from PyQt5 import QtCore

class MonitoringController:
    def __init__(self, ui):
        self.ui = ui
        self.service = MonitoringService()

        # matplotlib Figure 4개 생성
        self.fig_voltage = Figure(figsize=(4, 3))
        self.fig_current = Figure(figsize=(4, 3))
        self.fig_power = Figure(figsize=(4, 3))
        self.fig_energy = Figure(figsize=(4, 3))

        self.canvas_voltage = FigureCanvas(self.fig_voltage)
        self.canvas_current = FigureCanvas(self.fig_current)
        self.canvas_power = FigureCanvas(self.fig_power)
        self.canvas_energy = FigureCanvas(self.fig_energy)

        # UI Frame에 canvas 넣기
        self._setup_canvas()

        # 그래프 기본 모드 설정
        self.ui.comboBox_interval.currentTextChanged.connect(self.update_graphs)

        # 초기 로드
        self.update_graphs()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start(60000)

    def _setup_canvas(self):
        # 전압
        layout = self.ui.frame.layout()
        if layout is None:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.frame)
        layout.addWidget(self.canvas_voltage)

        # 전류
        layout = self.ui.frame_3.layout()
        if layout is None:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.frame_3)
        layout.addWidget(self.canvas_current)

        # 전력
        layout = self.ui.frame_2.layout()
        if layout is None:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.frame_2)
        layout.addWidget(self.canvas_power)

        # 누적 전력량
        layout = self.ui.frame_4.layout()
        if layout is None:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.frame_4)
        layout.addWidget(self.canvas_energy)

    def get_time_format(self, mode):
        """
        interval 모드에 맞는 matplotlib 시간 포맷 리턴
        """
        if mode == "1분":
            return mdates.DateFormatter('%H:%M')
        elif mode == "10분":
            return mdates.DateFormatter('%H:%M')
        elif mode == "1시간":
            return mdates.DateFormatter('%H')
        elif mode == "24시간":
            return mdates.DateFormatter('%m-%d')
        else:
            return mdates.DateFormatter('%m-%d %H:%M')
    
    def update_graphs(self):
        mode = self.ui.comboBox_interval.currentText()
        LogManager.instance().log(f"그래프 주기 변경: {mode}")
        df = self.service.get_graph_data(mode)

        if df is None or df.empty:
            return

        # ===== 전압 =====
        self.fig_voltage.clear()
        ax1 = self.fig_voltage.add_subplot(111)
        ax1.plot(df["ts"], df["solar_v"], color="#930B0D", linewidth=1.5)
        ax1.set_ylabel("Voltage")
        ax1.grid(True)
        ax1.tick_params(axis='x', labelsize=8)
        formatter = self.get_time_format(mode)
        ax1.xaxis.set_major_formatter(formatter)
        self.canvas_voltage.draw()

        # ===== 전류 =====
        self.fig_current.clear()
        ax2 = self.fig_current.add_subplot(111)
        ax2.plot(df["ts"], df["solar_i"], color="#0C6AA4", linewidth=1.5)
        ax2.set_ylabel("Current")
        ax2.grid(True)
        ax2.tick_params(axis='x', labelsize=8)
        formatter = self.get_time_format(mode)
        ax2.xaxis.set_major_formatter(formatter)
        self.canvas_current.draw()

        # ===== 전력 =====
        self.fig_power.clear()
        ax3 = self.fig_power.add_subplot(111)
        ax3.plot(df["ts"], df["solar_p"], color="#4C934C", linewidth=1.5)
        ax3.set_ylabel("Power")
        ax3.grid(True)
        ax3.tick_params(axis='x', labelsize=8)
        formatter = self.get_time_format(mode)
        ax3.xaxis.set_major_formatter(formatter)
        self.canvas_power.draw()

        # ===== 누적 전력량 =====
        self.fig_energy.clear()
        ax4 = self.fig_energy.add_subplot(111)
        df["cumulative_energy"] = df["solar_p"].cumsum() / 60  # Wh
        ax4.plot(df["ts"], df["cumulative_energy"], color="#740399", linewidth=1.5)
        ax4.set_ylabel("Energy")
        ax4.grid(True)
        ax4.tick_params(axis='x', labelsize=8)
        formatter = self.get_time_format(mode)
        ax4.xaxis.set_major_formatter(formatter)
        self.canvas_energy.draw()

    def show_csv_table(self):
    # 최근 24시간 데이터 가져오기
        df = self.service.get_raw_last_24h()
        if df is None or df.empty:
            print("⚠️ CSV 표시할 데이터 없음")
            return

        # 팝업 다이얼로그 생성
        dialog = QDialog()
        dialog.setWindowTitle("최근 24시간 데이터")
        dialog.resize(900, 600)

        layout = QVBoxLayout(dialog)

        # 테이블 생성
        table = QTableWidget()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)

        # 테이블에 데이터 채우기
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = str(df.iat[row, col])
                table.setItem(row, col, QTableWidgetItem(value))

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec_()