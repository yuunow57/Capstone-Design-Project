from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

class LogController(QObject):
    append_signal = pyqtSignal(str)

    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        # UI 요소
        self.textbox = ui.findChild(type(ui.textEdit), "textEdit")
        self.btn_save = ui.findChild(type(ui.pushButton_2), "pushButton_2")
        self.btn_clear = ui.findChild(type(ui.pushButton_3), "pushButton_3")

        # 버튼 기능 연결
        self.btn_save.clicked.connect(self.save_logs)
        self.btn_clear.clicked.connect(self.clear_logs)

        # 백그라운드 스레드 → UI 를 위한 시그널 연결
        self.append_signal.connect(self._append_text)

    def add_log(self, message: str):
        """백그라운드 스레드에서도 안전하게 호출 가능"""
        self.append_signal.emit(message)

    def _append_text(self, text):
        """UI 스레드에서 실행"""
        self.textbox.append(text)

    def save_logs(self):
        path, _ = QFileDialog.getSaveFileName(None, "로그 저장", "", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.textbox.toPlainText())

    def clear_logs(self):
        self.textbox.clear()
