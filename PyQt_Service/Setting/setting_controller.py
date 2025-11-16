from PyQt5.QtWidgets import QMessageBox
from .serial_manager import SerialManager
from .command_service import CommandService
from PyQt_Service.Log.log_manager import LogManager


class SettingController:
    def __init__(self, ui, system_state):
        self.ui = ui
        self.system_state = system_state

        # Serial
        self.serial = SerialManager()
        self.command = CommandService(self.serial)

        self._connect_ui()
        self.refresh_ports()

    def _connect_ui(self):

        # USB
        self.ui.btn_refresh_port.clicked.connect(self.refresh_ports)
        self.ui.connect_button.clicked.connect(self.connect_serial)

        # 파일럿 램프
        self.ui.btn_pilot_green.clicked.connect(self.pilot_green)
        self.ui.btn_pilot_red.clicked.connect(self.pilot_red)
        self.ui.btn_pilot_off.clicked.connect(self.pilot_off)

        # 할로겐
        self.ui.btn_halogen_on.clicked.connect(self.halogen_on)
        self.ui.btn_halogen_off.clicked.connect(self.halogen_off)

        # 선풍기 상용
        self.ui.chk_fan_commercial_on.clicked.connect(self.fan_commercial_on)
        self.ui.chk_fan_commercial_off.clicked.connect(self.fan_commercial_off)

        # 선풍기 배터리
        self.ui.chk_fan_battery_on.clicked.connect(self.fan_battery_on)
        self.ui.chk_fan_battery_off.clicked.connect(self.fan_battery_off)

        # 모니터링 명령어
        self.ui.btn_battery_voltage.clicked.connect(self.command.print_battery_voltage)
        self.ui.btn_vcmon_data.clicked.connect(self.command.print_vcmon_data)
        self.ui.btn_system_status.clicked.connect(self.command.print_system_status)
        self.ui.btn_button_state.clicked.connect(self.command.print_all_voltages)

        # VC_MON_LC 제어
        self.ui.btn_data_reset.clicked.connect(self.command.reset_vcmon_data)
        self.ui.btn_auto_send_start.clicked.connect(self.command.start_vcmon_auto)
        self.ui.btn_auto_send_stop.clicked.connect(self.command.stop_vcmon_auto)

    # =====================
    # USB 포트 새로고침
    # =====================

    def refresh_ports(self):
        ports = self.serial.list_ports()
        self.ui.port_combo.clear()

        if not ports:
            self.ui.port_combo.addItem("포트 없음")
            LogManager.instance().log("포트 없음 – 검색 결과 0개")
            return

        for p in ports:
            # 💡 1) ListPortInfo 객체인 경우
            if hasattr(p, "device"):
                device = p.device
                desc = p.description if hasattr(p, "description") else "Unknown Device"

            # 💡 2) tuple 형태인 경우
            elif isinstance(p, tuple):
                # 예: ("COM3", "USB-SERIAL CH340", something)
                device = p[0]
                desc = p[1] if len(p) > 1 else "Unknown Device"

            else:
                # 완전 예외적일 때
                device = str(p)
                desc = "Unknown Device"

            text = f"{device} ({desc})"
            self.ui.port_combo.addItem(text)

        LogManager.instance().log(f"포트 목록 새로고침 (총 {len(ports)}개)")

    # =====================
    # USB 연결
    # =====================

    def connect_serial(self):
        selected = self.ui.port_combo.currentText()

        if selected == "포트 없음":
            LogManager.instance().log("포트 연결 실패 – 선택된 포트 없음")
            self.ui.label_connect_status.setText("연결 X")
            self.ui.label_connect_status.setStyleSheet("color:#930B0D;")
            return

        # "COM3 (CH340 USB-SERIAL)" → "COM3"만 추출
        port = selected.split(" ")[0]

        ok = self.serial.connect(port)

        if ok:
            self.ui.label_connect_status.setText("연결됨")
            self.ui.label_connect_status.setStyleSheet("color:#0B930F;")
            LogManager.instance().log(f"포트 연결 성공 ({port})")
        else:
            self.ui.label_connect_status.setText("연결 X")
            self.ui.label_connect_status.setStyleSheet("color:#930B0D;")
            LogManager.instance().log(f"포트 연결 실패 ({port})")

    # =====================
    # 파일럿 램프
    # =====================

    def pilot_green(self):
        if self.command.pilot_green():
            self.system_state["pilot_green"] = True
            self.system_state["pilot_red"] = False

    def pilot_red(self):
        if self.command.pilot_red():
            self.system_state["pilot_red"] = True
            self.system_state["pilot_green"] = False

    def pilot_off(self):
        if self.command.pilot_off():
            self.system_state["pilot_green"] = False
            self.system_state["pilot_red"] = False

    # =====================
    # 할로겐
    # =====================

    def halogen_on(self):
        if self.command.halogen_on():
            self.system_state["halogen"] = True

    def halogen_off(self):
        if self.command.halogen_off():
            self.system_state["halogen"] = False

    # =====================
    # 상용 선풍기
    # =====================

    def fan_commercial_on(self):
        if self.command.fan_commercial_on():
            self.system_state["fan_commercial"] = True

    def fan_commercial_off(self):
        if self.command.fan_commercial_off():
            self.system_state["fan_commercial"] = False

    # =====================
    # 배터리 선풍기
    # =====================

    def fan_battery_on(self):
        if self.command.fan_battery_on():
            self.system_state["fan_battery"] = True

    def fan_battery_off(self):
        if self.command.fan_battery_off():
            self.system_state["fan_battery"] = False
