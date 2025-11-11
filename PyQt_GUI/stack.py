from PyQt5 import QtWidgets, uic
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        page_battery = uic.loadUi(os.path.join(base_path, "log.ui"))
        page_setting = uic.loadUi(os.path.join(base_path, "new_set.ui"))
        page_info = uic.loadUi(os.path.join(base_path, "information.ui"))


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
