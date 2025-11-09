import serial
from PyQt5.QtWidgets import QMessageBox


class SensorResetManager:
    """
    센서 리셋 버튼 동작을 담당하는 클래스.
    (Reset Sensor 버튼 클릭 시 아두이노로 리셋 명령 전송)
    """

    def __init__(self, ui, port=None):
        """
        ui : Setting 페이지 전체 UI 객체
        port : USBPortManager 등에서 전달받을 시리얼 포트 (옵션)
        """
        self.ui = ui
        self.serial_port = port  # 아직 USB 연결 안 되어도 상관없음

        # ✅ setting.ui 기준 버튼 이름 = btn_reconnect
        self.ui.btn_reconnect.clicked.connect(self.reset_sensor)

    # -------------------- 센서 리셋 --------------------
    def reset_sensor(self):
        """센서 리셋 명령 전송 또는 내부 초기화"""
        reply = QMessageBox.question(
            None,
            "센서 리셋",
            "정말로 센서를 리셋하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return

        # 시리얼 포트가 있으면 명령 전송
        if self.serial_port:
            try:
                with serial.Serial(self.serial_port, 9600, timeout=1) as ser:
                    ser.write(b"RESET\n")
                QMessageBox.information(None, "센서 리셋", "센서가 성공적으로 리셋되었습니다.")
                print("✅ 센서 리셋 명령 전송 완료")
            except Exception as e:
                QMessageBox.critical(None, "리셋 실패", f"센서를 리셋할 수 없습니다.\n\n에러: {e}")
        else:
            QMessageBox.information(None, "센서 리셋", "내부 센서 데이터가 초기화되었습니다.")
            print("✅ 내부 데이터 초기화 완료")
