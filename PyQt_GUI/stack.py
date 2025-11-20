# PyQt_GUI/stack.py

from PyQt5 import QtWidgets, uic
import sys, os

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Controller import
from PyQt_Service.Monitoring.monitoring_controller import MonitoringController
from PyQt_Service.Setting.setting_controller import SettingController
from PyQt_Service.Dashboard.dashboard_controller import DashboardController
from PyQt_Service.Log.log_controller import LogController
from PyQt_Service.Log.log_manager import LogManager
from PyQt_Service.Monitoring.monitoring_collector import MonitoringCollector


class StackApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        base_path = os.path.dirname(os.path.abspath(__file__))

        # main UI 로드 (대시보드 메인 윈도우)
        uic.loadUi(os.path.join(base_path, "dashboard.ui"), self)
        self.stack: QtWidgets.QStackedWidget = self.findChild(
            QtWidgets.QStackedWidget, "stackedWidget"
        )

        # 각 페이지 로드
        dashboard_page = self.stack.widget(0)  # 대시보드 첫 페이지
        page_sungp = uic.loadUi(os.path.join(base_path, "sungp.ui"))
        page_log = uic.loadUi(os.path.join(base_path, "log.ui"))
        page_setting = uic.loadUi(os.path.join(base_path, "new_set.ui"))
        page_info = uic.loadUi(os.path.join(base_path, "information.ui"))

        # stackedWidget 에 페이지 등록
        self.stack.addWidget(page_sungp)
        self.stack.addWidget(page_log)
        self.stack.addWidget(page_setting)
        self.stack.addWidget(page_info)

        # 시스템 상태 (대시보드 + 설정 페이지에서 공유)
        self.system_state = {
            "pilot": "RED",          # 기본 RED
            "halogen": False,
            "fan_commercial": False,
            "fan_battery": False,
        }

        # 🔹 로그 컨트롤러 생성 + LogManager 에 등록
        self.log_controller = LogController(page_log)
        LogManager.instance().set_controller(self.log_controller)

        # 🔹 모니터링 컨트롤러
        self.monitoring_controller = MonitoringController(page_sungp)
        # CSV 보기 버튼
        page_sungp.btn_show_csv.clicked.connect(
            self.monitoring_controller.show_csv_table
        )

        # 🔹 설정 컨트롤러
        self.setting_controller = SettingController(page_setting, self.system_state)

        self.collector = MonitoringCollector(self.setting_controller.serial)
        self.collector.start()

        # 🔹 대시보드 컨트롤러
        self.dashboard_controller = DashboardController(
            dashboard_page,
            self.setting_controller.serial,
            self.setting_controller.system_state,
        )
        
        self.setting_controller.dashboard = self.dashboard_controller

        # 페이지 리스트 (버튼 순서와 매칭)
        self.pages = [dashboard_page, page_sungp, page_log, page_setting, page_info]

        # 왼쪽 메뉴 버튼들
        self.buttons = [
            self.pushButton,  # 대시보드
            self.pushButton_2,  # 태양광 M
            self.pushButton_3,  # 로그
            self.pushButton_4,  # 설정
            self.pushButton_5,  # 정보
        ]

        # 버튼 클릭 시 페이지 변경
        for btn, page in zip(self.buttons, self.pages):
            btn.clicked.connect(lambda _, p=page: self.change_page(p))

        # 종료 버튼
        self.pushButton_6.clicked.connect(self.close)
        self.pushButton_6.setStyleSheet(
            "text-align: left; padding-left: 10px; color: #333333;"
        )

        # 초기 페이지: 대시보드
        self.change_page(self.pages[0])

    def change_page(self, page):
        self.stack.setCurrentWidget(page)
        idx = self.pages.index(page)
        for i, btn in enumerate(self.buttons):
            style = btn.styleSheet()
            style = remove_color_from_stylesheet(style)
            if i == idx:
                btn.setStyleSheet(style + "color: #9E1010;")
            else:
                btn.setStyleSheet(style + "color: #333333;")

    def closeEvent(self, event):
        """
        프로그램 종료 시 Serial 포트가 열려 있다면 자동으로 닫아주는 함수.
        포트가 닫히지 않으면 운영체제가 포트를 계속 점유하여
        다음 실행에서 연결이 안 되는 문제를 방지한다.
        """
        try:
            if hasattr(self, "setting_controller"):
                serial = self.setting_controller.serial
                if serial.port and serial.port.is_open:
                    serial.port.close()
                    print("🔌 시리얼 포트 정상 종료됨")
        except Exception as e:
            print(f"⚠️ 시리얼 포트 종료 중 오류: {e}")

        event.accept()


def remove_color_from_stylesheet(style):
    import re

    return re.sub(r"color\s*:\s*#[0-9A-Fa-f]+;", "", style)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StackApp()
    window.show()
    sys.exit(app.exec_())
