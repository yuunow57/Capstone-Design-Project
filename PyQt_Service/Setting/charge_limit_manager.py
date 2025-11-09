from PyQt5.QtWidgets import QMessageBox


class ChargeLimitManager:
    """
    배터리 충전 한계(%)를 설정하는 매니저 클래스.
    사용자가 입력칸에 수치를 입력하고 '적용' 버튼을 누르면 작동.
    """

    def __init__(self, ui):
        """
        ui : Setting 페이지 전체 UI 객체
        (edit_battery_limit: 입력칸, pushButton: 적용 버튼)
        """
        self.ui = ui
        self.charge_limit = None  # 현재 설정된 충전 한계

        # 버튼 연결
        self.ui.pushButton.clicked.connect(self.apply_charge_limit)

    # -------------------- 충전 한계 적용 --------------------
    def apply_charge_limit(self):
        """입력된 충전 한계값(%)을 검증 후 적용"""
        input_text = self.ui.edit_battery_limit.text().strip()

        # 입력값 확인
        if not input_text:
            QMessageBox.warning(None, "입력 오류", "충전 한계값을 입력하세요.")
            return

        try:
            limit = float(input_text)
        except ValueError:
            QMessageBox.warning(None, "입력 오류", "숫자만 입력 가능합니다.")
            return

        # 범위 검사 (0~100%)
        if not 0 <= limit <= 100:
            QMessageBox.warning(None, "범위 오류", "충전 한계는 0~100% 사이여야 합니다.")
            return

        # 적용
        self.charge_limit = limit
        QMessageBox.information(None, "충전 한계 설정", f"충전 한계가 {limit:.1f}%로 설정되었습니다.")
        print(f"✅ 충전 한계 적용: {limit:.1f}%")

        # 입력칸 초기화 (선택사항)
        # self.ui.edit_battery_limit.clear()
