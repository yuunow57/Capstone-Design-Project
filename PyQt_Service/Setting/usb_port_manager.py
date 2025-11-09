import serial.tools.list_ports
from PyQt5.QtWidgets import QMessageBox


class USBPortManager:
    """
    USB 포트 목록을 가져오고,
    사용자가 선택한 포트를 저장 및 적용하는 클래스.
    """

    def __init__(self, ui):
        """
        ui : Setting 페이지의 전체 UI 객체
        (comboBox_2: 포트 선택, pushButton: 적용 버튼)
        """
        self.ui = ui
        self.selected_port = None

        # ✅ 초기 포트 목록 불러오기
        self.update_port_list()

        # ✅ UI 이벤트 연결
        # 드롭박스에서 포트 선택 시
        self.ui.comboBox_2.currentIndexChanged.connect(self.on_port_selected)

        # “적용” 버튼 연결 (지금 setting.ui에서는 배터리 한계 적용 버튼도 pushButton이라
        # 나중에 USB용 버튼 추가되면 btn_apply_usb로 바꾸는 게 좋음)
        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.clicked.connect(self.apply_usb_port)

    # -------------------- USB 포트 목록 갱신 --------------------
    def update_port_list(self):
        """시스템에 연결된 USB 포트 목록을 comboBox_2에 표시"""
        self.ui.comboBox_2.clear()

        ports = serial.tools.list_ports.comports()
        if not ports:
            self.ui.comboBox_2.addItem("⚠️ 포트 없음")
            return

        for port in ports:
            self.ui.comboBox_2.addItem(port.device)

        # 기본 선택값 지정
        self.selected_port = self.ui.comboBox_2.currentText()

    # -------------------- 포트 선택 시 --------------------
    def on_port_selected(self):
        """사용자가 드롭박스에서 포트를 선택했을 때 호출"""
        current_text = self.ui.comboBox_2.currentText()
        if "⚠️" not in current_text:
            self.selected_port = current_text
            print(f"✅ 선택된 포트: {self.selected_port}")

    # -------------------- 적용 버튼 --------------------
    def apply_usb_port(self):
        """선택한 포트를 실제 시스템에 적용"""
        if not self.selected_port:
            QMessageBox.warning(None, "USB 포트 설정", "적용할 포트를 선택하세요.")
            return

        try:
            # 예시: 포트 연결 테스트
            ser = serial.Serial(self.selected_port, 9600, timeout=1)
            ser.close()

            QMessageBox.information(None, "USB 포트 설정", f"{self.selected_port} 포트가 성공적으로 적용되었습니다.")
            print(f"✅ {self.selected_port} 포트 연결 테스트 성공")
        except Exception as e:
            QMessageBox.critical(None, "USB 포트 오류", f"포트를 적용할 수 없습니다.\n\n에러: {e}")
