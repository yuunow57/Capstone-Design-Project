from PyQt5 import QtWidgets, uic
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt_Service.Setting import SettingController
from PyQt_Service.Monitoring import MonitoringController
from PyQt_Service.Dashboard import DashboardController

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

        sungp_csv   = os.path.join(base_path, "../PyQt_Service/Monitoring/sample/solar_data.csv")
        battery_csv = os.path.join(base_path, "../PyQt_Service/Monitoring/sample/battery_data.csv")

        # 컨트롤러 연결부
        self.setting_controller = SettingController(page_setting)
        
        self.sungp_controller   = MonitoringController(page_sungp, sungp_csv)
        self.battery_controller = MonitoringController(page_battery, battery_csv)

        self.dashboard_controller = DashboardController(dashboard_page, sungp_csv)

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
        self.pushButton_6.setStyleSheet("text-align: left; padding-left: 10px; color: #333333;") ## 버튼 6 스타일

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
        # 기존 스타일 가져오기
            style = btn.styleSheet()
        # 색상만 바꾸기 위해 기존 style에서 color 제거
            style = remove_color_from_stylesheet(style)
          # 색상 추가
            if i == idx:
                btn.setStyleSheet(style + "color: #9E1010;")
            else:
                btn.setStyleSheet(style + "color: #333333;")



def remove_color_from_stylesheet(style):
    import re
    # 기존 style에 color 속성이 있으면 제거
    return re.sub(r'color\s*:\s*#[0-9A-Fa-f]+;', '', style)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StackApp()
    window.show()
    sys.exit(app.exec_())
