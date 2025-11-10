from PyQt5 import QtWidgets
import pandas as pd, os
from ..Monitoring.data_resampler import DataResampler
from ..Monitoring.graph_manager import GraphManager



class DashboardGraphManager:
    """대시보드의 미니 그래프(전압/전류/전력량)"""
    def __init__(self, host_widget, csv_path):
        self.host = host_widget
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_path, "../Monitoring/sample/solar_data.csv")
        self.df = pd.read_csv(self.csv_path, encoding="cp949")

        if self.host:
            layout = self.host.layout() or QtWidgets.QVBoxLayout(self.host)
            layout.setContentsMargins(8,8,8,8)
            self.graph = GraphManager(parent=self.host)
            layout.addWidget(self.graph)

    def update_graph(self):
        if not self.host or self.df.empty:
            return
        res = DataResampler(self.df).resample("1시간")   # 1시간 주기, 최근 24시간
        if res.empty:
            return

        # 컬럼명 맵핑
        col_v  = "전압(V)"
        col_a  = "전류(A)"
        col_pw = "전력량(W)"

        self.graph.ax.clear()
        self.graph.ax.plot(res["timestamp"], res[col_v], color="#930B0D")
        self.graph.ax.plot(res["timestamp"], res[col_a], color="#0C6AA4")
        self.graph.ax.plot(res["timestamp"], res[col_pw],color="#4C934C")
        self.graph.ax.set_ylim(bottom=0)
        self.graph.ax.tick_params(axis="x", labelrotation=30)
        self.graph.ax.grid(True, linestyle="--", alpha=0.3)
        self.graph.draw()
