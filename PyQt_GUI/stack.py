# battery_graph.py에서 BatteryGraphWidget은 그대로 사용
# 단, 각 그래프를 개별 위젯으로 만들 수 있게 조금 수정 필요

from PyQt5 import QtWidgets, uic
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from battery_graph import BatteryGraphWidget
from PyQt_Service.Setting import SettingController

class StackApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        base_path = os.path.dirname(os.path.abspath(__file__))

        # main UI 로드
        uic.loadUi(os.path.join(base_path, "dashboard.ui"), self)
        self.stack = self.findChild(QtWidgets.QStackedWidget, "stackedWidget")

        # 기존 페이지들
        dashboard_page = self.stack.widget(0)
        page_sungp = uic.loadUi(os.path.join(base_path, "sungp.ui"))
        page_battery = uic.loadUi(os.path.join(base_path, "battery.ui"))
        page_setting = uic.loadUi(os.path.join(base_path, "setting.ui"))
        page_info = uic.loadUi(os.path.join(base_path, "information.ui"))

        # --- 배터리 페이지에 그래프 넣기 ---
        # 프레임 이름 F_1 ~ F_4
        # self.graph_voltage = BatteryGraphWidget(graph_type="voltage")
        # self.graph_current = BatteryGraphWidget(graph_type="current")
        # self.graph_maxcurrent = BatteryGraphWidget(graph_type="maxcurrent")
        # self.graph_total = BatteryGraphWidget(graph_type="total")

        # 각 프레임 안에 넣기
        # for frame, graph in zip(
        #     [page_battery.F_1, page_battery.F_2, page_battery.F_3, page_battery.F_4],
        #     [self.graph_voltage, self.graph_current, self.graph_maxcurrent, self.graph_total]
        # ):
        #     layout = QtWidgets.QVBoxLayout(frame)
        #     layout.setContentsMargins(0,0,0,0)  # 프레임에 꽉 차게
        #     layout.addWidget(graph)


        self.setting_controller = SettingController(page_setting)
        

        # stackedWidget에 추가
        self.stack.addWidget(page_sungp)
        self.stack.addWidget(page_battery)
        self.stack.addWidget(page_setting)
        self.stack.addWidget(page_info)

        # 페이지 리스트
        self.pages = [dashboard_page, page_sungp, page_battery, page_setting, page_info]

        # 버튼 리스트
        self.buttons = [self.pushButton, self.pushButton_2, self.pushButton_3,
                        self.pushButton_4, self.pushButton_5]

        # 버튼 연결
        for btn, page in zip(self.buttons, self.pages):
            btn.clicked.connect(lambda _, p=page: self.change_page(p))

        # 종료 버튼
        self.pushButton_6.clicked.connect(self.close)

        # 초기 페이지
        self.change_page(self.pages[0])

    #

    def update_interval(self, value):
        print(f"그래프 업데이트 주기 변경: {value}")
        self.batteryGraph.set_update_interval(value)

    def on_interval_changed(self, page_setting):
        text = page_setting.comboBox.currentText()
        print(f"Update interval set to: {text}")

    def on_port_changed(self, page_setting):
        port = page_setting.comboBox_2.currentText()
        print(f"Serial port set to: {port}")


    def change_page(self, page):
        self.stack.setCurrentWidget(page)
        idx = self.pages.index(page)
        for i, btn in enumerate(self.buttons):
            if i == idx:
                btn.setStyleSheet("color: red; font-weight: bold;")
            else:
                btn.setStyleSheet("color: black; font-weight: normal;")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StackApp()
    window.show()
    sys.exit(app.exec_())
