from PyQt5.QtWidgets import QMessageBox


class VoltageThresholdManager:
    """
    배터리 임계 전압을 설정하고 적용하는 클래스.
    사용자가 전압 입력 후 '적용' 버튼을 클릭하면 동작.
    """

    def __init__(self, ui):
        """
        ui : Setting 페이지 전체 UI 객체
        (edit_threshold_voltage: 입력칸, btn_apply_voltage: 적용 버튼)
        """
        self.ui = ui
        self.threshold_voltage = None  # 현재 설정된 임계 전압 값

        # 버튼 이벤트 연결
        # self.ui.btn_apply_voltage.clicked.connect(self.apply_voltage_threshold)

    # -------------------- 임계 전압 적용 --------------------
    def apply_voltage_threshold(self):
        """입력된 임계 전압을 검증 후 적용"""
        input_text = self.ui.edit_threshold_voltage.text().strip()

        # 입력값 검증
        if not input_text:
            QMessageBox.warning(None, "입력 오류", "임계 전압값을 입력하세요.")
            return

        try:
            voltage = float(input_text)
        except ValueError:
            QMessageBox.warning(None, "입력 오류", "숫자만 입력 가능합니다.")
            return

        # 합리적인 전압 범위 제한 (예: 2.5V~5.0V)
        if not 2.5 <= voltage <= 5.0:
            QMessageBox.warning(None, "범위 오류", "임계 전압은 2.5V~5.0V 사이여야 합니다.")
            return

        # 값 저장 및 피드백
        self.threshold_voltage = voltage
        QMessageBox.information(None, "임계 전압 설정", f"임계 전압이 {voltage:.2f}V로 설정되었습니다.")
        print(f"✅ 임계 전압 적용: {voltage:.2f}V")

        # 입력창 초기화 (선택 사항)
        # self.ui.edit_threshold_voltage.clear()
