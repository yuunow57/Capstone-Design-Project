from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from .clock_manager import ClockManager
from .battery_status_manager import BatteryStatusManager
from .load_power_manager import LoadPowerManager
from .connection_status_manager import ConnectionStatusManager
from .warning_manager import WarningManager
from .dashboard_graph_manager import DashboardGraphManager

class DashboardController:
    """대시보드 페이지 총괄"""
    def __init__(self, ui_root: QtWidgets.QWidget, csv_path: str):
        self.ui_root = ui_root
        self.csv_path = csv_path
        print("🎨 대시보드 컨트롤러 초기화 시작")

        # 필요한 위젯들을 objectName으로 찾아서 보관
        self.lbl_soc  = self.ui_root.findChild(QtWidgets.QLabel,  "label_2")
        self.lbl_time = self.ui_root.findChild(QtWidgets.QLabel,  "label_3")
        self.lbl_load = self.ui_root.findChild(QtWidgets.QLabel,  "label_4")
        self.lbl_conn = self.ui_root.findChild(QtWidgets.QLabel,  "label_5")
        self.lbl_warn = self.ui_root.findChild(QtWidgets.QLabel,  "label_6")
        self.graph_host = self.ui_root.findChild(QtWidgets.QWidget, "widget_graph_area")

        # 매니저들은 위젯을 직접 주입받는다
        self.clock          = ClockManager(self.lbl_time)
        self.battery_status = BatteryStatusManager(self.lbl_soc,  csv_path)
        self.load_power     = LoadPowerManager(self.lbl_load,     csv_path)
        self.connection     = ConnectionStatusManager(self.lbl_conn)
        self.warning        = WarningManager(self.lbl_warn)
        self.graph          = DashboardGraphManager(self.graph_host, csv_path)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)

    def update_dashboard(self):
        # 각 위젯이 존재할 때만 업데이트 (None 안전)
        if self.lbl_time: self.clock.update_time()
        if self.lbl_soc:  self.battery_status.update_status()
        if self.lbl_load: self.load_power.update_value()
        if self.lbl_conn: self.connection.update_status()
        if self.lbl_warn: self.warning.update_message()
        if self.graph_host: self.graph.update_graph()
