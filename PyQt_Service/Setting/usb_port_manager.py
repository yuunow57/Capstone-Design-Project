import serial.tools.list_ports
from PyQt5.QtWidgets import QMessageBox


class USBPortManager:
    """
    USB 포트 목록을 가져오고,
    사용자가 선택한 포트를 저장 및 적용하는 클래스.
    """

    def __init__(self, ui):
        """
        ui : PyQt Designer에서 변환된 UI 객체 (QComboBox, QPushButton 등을 포함)
        """
        self.ui = ui
        self.selected_port = None

        # 초기 포트 목록 불러오기
        self.update_port_list()

        # UI 이벤트 연결
        self.ui.comboBox_usb_port.currentIndexChanged.connect(self.on_port_selected)
        self.ui.btn_apply_usb.clicked.connect(self.apply_usb_port)

    # -------------------- USB 포트 목록 갱신 --------------------
    def update_port_list(self):
        """시스템에 연결된 USB 포트 목록을 QComboBox에 표시"""
        self.ui.comboBox_usb_port.clear()

        ports = serial.tools.list_ports.comports()
        if not ports:
            self.ui.comboBox_usb_port.addItem("⚠️ 포트 없음")
            return

        for port in ports:
            self.ui.comboBox_usb_port.addItem(port.device)

    # -------------------- 포트 선택 시 --------------------
    def on_port_selected(self):
        """사용자가 드롭박스에서 포트를 선택했을 때 호출"""
        current_text = self.ui.comboBox_usb_port.currentText()
        if "⚠️" not in current_text:
            self.selected_port = current_text

    # -------------------- 적용 버튼 --------------------
    def apply_usb_port(self):
        """선택한 포트를 실제 시스템에 적용"""
        if not self.selected_port:
            QMessageBox.warning(None, "USB 포트 설정", "적용할 포트를 선택하세요.")
            return

        # (실제 포트 적용 로직 — 예: 시리얼 통신 초기화 등)
        try:
            # 예시: 포트 연결 테스트
            ser = serial.Serial(self.selected_port, 9600, timeout=1)
            ser.close()

            QMessageBox.information(None, "USB 포트 설정", f"{self.selected_port} 포트가 성공적으로 적용되었습니다.")
        except Exception as e:
            QMessageBox.critical(None, "USB 포트 오류", f"포트를 적용할 수 없습니다.\n\n에러: {e}")
