from PyQt5.QtWidgets import QMessageBox
from .serial_manager import SerialManager
from .command_service import CommandService
from PyQt_Service.Log.log_manager import LogManager


class SettingController:
    def __init__(self, ui, system_state):
        self.ui = ui
        self.system_state = system_state

        # StackApp 에서 대시보드 컨트롤러 주입 예정
        self.dashboard = None

        # Serial
        self.serial = SerialManager()
        self.command = CommandService(self.serial)

        self._connect_ui()
        self.refresh_ports()

    # ─────────────────────────────────────
    # 대시보드에 UI 갱신 요청
    # ─────────────────────────────────────
    def _notify_dashboard(self):
        if self.dashboard is not None:
            try:
                self.dashboard.update_ui()
            except Exception as e:
                LogManager.instance().log(f"대시보드 갱신 오류: {e}")

    # ─────────────────────────────────────
    # UI 연결
    # ─────────────────────────────────────
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

        # ⭐ 로그가 필요한 버튼 3개 (j, k, u)
        self.ui.btn_battery_voltage.clicked.connect(self.command.print_battery_voltage)
        self.ui.btn_vcmon_data.clicked.connect(self.command.print_vcmon_data)
        self.ui.btn_system_status.clicked.connect(self.command.print_system_status)

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
            device = p.device if hasattr(p, "device") else str(p)
            desc = p.description if hasattr(p, "description") else "Unknown Device"
            self.ui.port_combo.addItem(f"{device} ({desc})")

        LogManager.instance().log(f"포트 목록 새로고침 ({len(ports)}개)")

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

        self._notify_dashboard()

    # =====================
    # 파일럿 램프 (소프트웨어 상태만 변경)
    # =====================
    def pilot_green(self):
        self.command.pilot_green()
        self.system_state["pilot"] = "RED"
        self._notify_dashboard()

    def pilot_red(self):
        self.command.pilot_red()
        self.system_state["pilot"] = "GREEN"
        self._notify_dashboard()

    def pilot_off(self):
        self.command.pilot_off()
        self.system_state["pilot"] = "OFF"
        self._notify_dashboard()

    # =====================
    # 할로겐
    # =====================
    def halogen_on(self):
        if self.command.halogen_on():
            self.system_state["halogen"] = True
            self._notify_dashboard()

    def halogen_off(self):
        if self.command.halogen_off():
            self.system_state["halogen"] = False
            self._notify_dashboard()

    # =====================
    # 상용 선풍기
    # =====================
    def fan_commercial_on(self):
        if self.command.fan_commercial_on():
            self.system_state["fan_commercial"] = True
            self._notify_dashboard()

    def fan_commercial_off(self):
        if self.command.fan_commercial_off():
            self.system_state["fan_commercial"] = False
            self._notify_dashboard()

    # =====================
    # 배터리 선풍기
    # =====================
    def fan_battery_on(self):
        if self.command.fan_battery_on():
            self.system_state["fan_battery"] = True
            self._notify_dashboard()

    def fan_battery_off(self):
        if self.command.fan_battery_off():
            self.system_state["fan_battery"] = False
            self._notify_dashboard()
