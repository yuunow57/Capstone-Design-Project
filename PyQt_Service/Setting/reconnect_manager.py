import serial
from PyQt5.QtWidgets import QMessageBox


class ReconnectManager:
    """
    통신 재연결 기능을 담당하는 클래스.
    (Reconnect 버튼 클릭 시, 시리얼 포트를 닫고 다시 연결 시도)
    """

    def __init__(self, ui, port=None):
        """
        ui : Setting 페이지 전체 UI 객체
        port : USBPortManager에서 전달받을 선택된 포트 (선택사항)
        """
        self.ui = ui
        self.serial_port = port
        self.connection = None

        # ✅ setting.ui 기준 버튼 이름 = btn_reconnect_2
        self.ui.btn_reconnect_2.clicked.connect(self.reconnect)

    # -------------------- 재연결 시도 --------------------
    def reconnect(self):
        """통신 재연결 로직"""
        if not self.serial_port:
            QMessageBox.warning(None, "통신 재연결", "선택된 포트가 없습니다.")
            return

        try:
            # 기존 연결 닫기
            if self.connection and self.connection.is_open:
                self.connection.close()

            # 새로운 연결 시도
            self.connection = serial.Serial(self.serial_port, 9600, timeout=1)
            QMessageBox.information(None, "통신 재연결", f"{self.serial_port} 포트에 재연결되었습니다.")
            print(f"✅ {self.serial_port} 포트 재연결 완료")

        except Exception as e:
            QMessageBox.critical(None, "통신 오류", f"재연결에 실패했습니다.\n\n에러: {e}")
