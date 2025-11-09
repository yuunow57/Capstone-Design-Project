import json
import os
from PyQt5.QtWidgets import QMessageBox


class ConfigApplyManager:
    """
    설정 적용 및 기본값 복원 기능을 담당하는 클래스.
    (Save / Default 버튼 클릭 시 설정 저장 또는 초기화 수행)
    """

    def __init__(self, ui):
        """
        ui : Setting 페이지 전체 UI 객체
        """
        self.ui = ui
        self.config_file = os.path.join(os.path.dirname(__file__), "user_config.json")

        # 버튼 연결
        self.ui.pushButton_2.clicked.connect(self.save_config)   # 적용하기 (Save)
        self.ui.pushButton_3.clicked.connect(self.restore_defaults)  # 기본값 복원 (Default)

        # 프로그램 시작 시 저장된 설정 불러오기
        self.load_config()

    # -------------------- 설정 저장 --------------------
    def save_config(self):
        """현재 UI의 값을 JSON 파일에 저장"""
        config = {
            "usb_port": self.ui.comboBox_2.currentText(),
            "charge_limit": self.ui.edit_battery_limit.text(),
            "threshold_voltage": self.ui.edit_threshold_voltage.text(),
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            QMessageBox.information(None, "설정 저장", "현재 설정이 저장되었습니다.")
            print("✅ 설정 저장 완료:", config)
        except Exception as e:
            QMessageBox.critical(None, "저장 오류", f"설정을 저장할 수 없습니다.\n\n에러: {e}")

    # -------------------- 설정 불러오기 --------------------
    def load_config(self):
        """프로그램 시작 시 기존 설정 불러오기"""
        if not os.path.exists(self.config_file):
            return  # 첫 실행 시 파일이 없을 수 있음

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 불러온 설정 UI에 반영
            self.ui.edit_battery_limit.setText(config.get("charge_limit", "85"))
            self.ui.edit_threshold_voltage.setText(config.get("threshold_voltage", "3.2"))

            # USB 포트 드롭박스는 실제 연결 포트와 다를 수 있으니 존재할 경우만 반영
            usb_text = config.get("usb_port", "")
            idx = self.ui.comboBox_2.findText(usb_text)
            if idx != -1:
                self.ui.comboBox_2.setCurrentIndex(idx)

            print("✅ 설정 불러오기 완료:", config)

        except Exception as e:
            QMessageBox.warning(None, "불러오기 오류", f"설정을 불러올 수 없습니다.\n\n에러: {e}")

    # -------------------- 기본값 복원 --------------------
    def restore_defaults(self):
        """모든 설정을 기본값으로 되돌림"""
        reply = QMessageBox.question(
            None,
            "기본값 복원",
            "모든 설정을 기본값으로 되돌리시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return

        # 기본값 설정
        self.ui.edit_battery_limit.setText("85")
        self.ui.edit_threshold_voltage.setText("3.2")
        self.ui.comboBox_2.setCurrentIndex(0)

        # JSON 파일도 갱신
        default_config = {
            "usb_port": self.ui.comboBox_2.currentText(),
            "charge_limit": "85",
            "threshold_voltage": "3.2",
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            QMessageBox.information(None, "기본값 복원", "기본값이 적용되었습니다.")
            print("✅ 기본값 복원 완료:", default_config)
        except Exception as e:
            QMessageBox.critical(None, "복원 오류", f"기본값을 저장할 수 없습니다.\n\n에러: {e}")
