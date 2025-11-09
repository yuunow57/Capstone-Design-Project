import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer

class BatteryGraphWidget(QWidget):
    def __init__(self, graph_type="voltage"):  # graph_type 기본값 지정
        super().__init__()

        self.graph_type = graph_type

        # layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 데이터 초기화
        self.max_points = 50
        self.time_data = list(range(self.max_points))
        self.voltage_data = [3.7]*self.max_points
        self.current_data = [3.7]*self.max_points
        self.maxcurrent_data = [3.7]*self.max_points
        self.total_data = [90]*self.max_points

        # PlotWidget 생성
        self.graph = pg.PlotWidget()
        self.layout.addWidget(self.graph)

        # 그래프 초기화
        self.setup_graph()

        # 타이머
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_graph_data)
        self.timer.start()

    def setup_graph(self):
        if self.graph_type == "voltage":
            self.line = self.graph.plot(self.time_data, self.voltage_data, pen=pg.mkPen('r', width=2))
            self.graph.setTitle("1S Module Voltage (V)")
        elif self.graph_type == "current":
            self.line = self.graph.plot(self.time_data, self.current_data, pen=pg.mkPen('g', width=2))
            self.graph.setTitle("2S Module Current (A)")
        elif self.graph_type == "maxcurrent":
            self.line = self.graph.plot(self.time_data, self.maxcurrent_data, pen=pg.mkPen('y', width=2))
            self.graph.setTitle("3S Module Max Current (A)")
        elif self.graph_type == "total":
            self.line = self.graph.plot(self.time_data, self.total_data, pen=pg.mkPen('b', width=3))
            self.graph.setTitle("Total Pack SOC (%)")
        self.graph.showGrid(x=True, y=True)

    def update_graph_data(self):
        if self.graph_type == "voltage":
            new_val = 3.7 + np.random.uniform(-0.1, 0.1)
            self.voltage_data.pop(0)
            self.voltage_data.append(new_val)
            self.line.setData(self.time_data, self.voltage_data)
        elif self.graph_type == "current":
            new_val = np.random.uniform(-40, 40)
            self.current_data.pop(0)
            self.current_data.append(new_val)
            self.line.setData(self.time_data, self.current_data)
        elif self.graph_type == "maxcurrent":
            new_val = np.random.uniform(0, 50)
            self.maxcurrent_data.pop(0)
            self.maxcurrent_data.append(new_val)
            self.line.setData(self.time_data, self.maxcurrent_data)
        elif self.graph_type == "total":
            new_val = self.total_data[-1] + np.random.uniform(-0.5, 0.5)
            new_val = np.clip(new_val, 0, 100)
            self.total_data.pop(0)
            self.total_data.append(new_val)
            self.line.setData(self.time_data, self.total_data)
