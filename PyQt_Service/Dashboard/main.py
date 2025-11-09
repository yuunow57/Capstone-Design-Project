import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtGui import QFont
import pyqtgraph as pg

# 프로젝트 내부 모듈 임포트
from dashboard_ui import Ui_MainWindow  # Qt Designer로 변환된 대시보드 UI 클래스
from db_manager import DatabaseManager  # 데이터베이스 연결 및 관리 모듈
from serial_manager import SerialManager  # 센서 데이터 통신/시뮬레이션 모듈
from collector_thread import DataCollector  # 백그라운드 데이터 수집 스레드 모듈


# 1. 사용자 정의 시간 축 클래스: 그래프 X축에 HH:MM 형식으로 시간을 표시하기 위한 Custom Axis Item
class TimeAxisItem(pg.AxisItem):
    """X축의 숫자(분, Sample Count)를 HH:MM 형식의 문자열로 변환하는 클래스"""

    def tickStrings(self, values, scale, spacing):
        strings = []
        for value in values:
            if value >= 0:
                minutes = int(value)
                hours = minutes // 60
                minutes = minutes % 60
                # HH:MM 형식으로 포맷팅 (00:00부터 경과된 시간)
                strings.append(f"{hours:02d}:{minutes:02d}")
            else:
                strings.append("")
        return strings


# 나머지 화면 UI 파일 임포트 (화면 통합 시 주석 해제 후 사용)
# from pv_status_ui import Ui_PVStatus
# from batt_status_ui import Ui_BattStatus
# from settings_ui import Ui_Settings
# from info_ui import Ui_Info

class EnergyPlatformApp(QMainWindow, Ui_MainWindow):
    """
    신재생에너지 관제 플랫폼의 메인 GUI 애플리케이션 클래스입니다.
    UI 초기화, 시스템 연결 관리, 데이터 실시간 업데이트를 담당합니다.
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Qt Designer에서 생성된 UI 로드

        self._init_system()
        self._init_ui_connections()
        self._init_clock()
        self._start_data_collection()

    def _init_system(self):
        """데이터베이스 및 통신 매니저 객체를 초기화하고 기본 설정값을 로드합니다."""
        self.db_manager = DatabaseManager()

        # DB에서 시스템 설정 로드 (갱신 주기 및 포트명)
        config = self.db_manager.get_config()
        port_name = config[4]
        refresh_rate_ms = config[1]

        self.serial_manager = SerialManager(port_name=port_name)
        self._refresh_rate_ms = refresh_rate_ms

        # 서브 화면 초기화 로직 (화면 통합 시 여기에 추가)
        # self._init_sub_pages()

    def _init_ui_connections(self):
        """대시보드의 위젯과 이벤트를 연결합니다."""

        # 화면 전환 버튼 연결 (화면 통합 시 여기에 추가)
        # self.btn_dashboard.clicked.connect(...)
        # ...
        self.btn_exit.clicked.connect(self.close)  # 프로그램 종료 버튼 연결

        # 대시보드 그래프 영역 초기화
        self._init_dashboard_graph()

    def _init_clock(self):
        """현재 시스템 시각을 1초마다 업데이트하는 타이머를 설정합니다."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

    def _update_time(self):
        """현재 시각을 UI의 lbl_current_time에 업데이트합니다."""
        current_time = QDateTime.currentDateTime().toString("현재 시각: yyyy-MM-dd hh:mm:ss")
        self.lbl_current_time.setText(current_time)

    def _init_dashboard_graph(self):
        """발전 전력 그래프 영역을 pyqtgraph 객체로 대체하고 초기 설정합니다."""

        # 1. 기존 UI 위젯 제거 및 PlotWidget 생성
        layout = self.graph_pv_power.parent().layout()
        if layout:
            layout.removeWidget(self.graph_pv_power)

        # PlotWidget 초기화 시 TimeAxisItem을 X축으로 사용
        self.time_axis = TimeAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(self.frame_3, axisItems={'bottom': self.time_axis})

        self.plot_widget.setGeometry(self.graph_pv_power.geometry())
        self.plot_widget.show()

        # 2. X축 (시간) 설정: 폰트 크기 조정
        axis_x = self.plot_widget.getAxis('bottom')
        axis_x.setTickFont(QFont("Arial", 7))

        # 3. Y축 (전력) 설정: 폰트 크기 조정 및 200W 간격으로 눈금 강제 설정 (겹침 문제 해결)
        axis_y = self.plot_widget.getAxis('left')
        axis_y.setTickFont(QFont("Arial", 7))
        axis_y.setTicks([[(i, str(i)) for i in range(-400, 401, 200)]])

        # 4. 그래프 레이블 설정
        self.plot_widget.setTitle("실시간 발전 전력 (W)", color="#5dade2")
        self.plot_widget.setLabel('left', '전력', units='W')
        self.plot_widget.setLabel('bottom', '시간 (HH:MM)')
        self.plot_widget.showGrid(x=True, y=True)

        # 5. 데이터 리스트 초기화
        self.time_data = []  # X축 (샘플 카운트)
        self.pv_power_data = []  # Y축 (전력 값)
        self.data_count = 0

        # 플롯 아이템 생성
        self.curve = self.plot_widget.plot(self.time_data, self.pv_power_data, pen='y')

    def _start_data_collection(self):
        """데이터 수집 스레드를 생성, 설정하고 시작합니다."""

        self.data_collector_thread = DataCollector(self.db_manager, self.serial_manager)

        # 스레드 시그널과 메인 윈도우 슬롯 연결
        self.data_collector_thread.data_received.connect(self._update_dashboard_data)
        self.data_collector_thread.connection_status_changed.connect(self._update_connection_status)

        self.data_collector_thread.set_refresh_rate(self._refresh_rate_ms)
        self.data_collector_thread.start()

    def _update_dashboard_data(self, data):
        """
        수집 스레드로부터 실시간 데이터를 받아 대시보드 위젯을 업데이트하는 슬롯 함수.
        UI 설계서의 표시 요구사항 및 경고 로직을 반영합니다.
        """

        # 1. 데이터 추출
        total_v = data.get('TOTAL_VOLTAGE', 0.0)
        pv_power = data.get('PV_POWER', 0.0)
        soc = data.get('SOC_TOTAL', 0.0)
        s1_v = data.get('BATT1_VOLTAGE', 0.0)
        s2_v = data.get('BATT2_VOLTAGE', 0.0)
        s3_v = data.get('BATT3_VOLTAGE', 0.0)
        load_power_v = total_v  # 부하 전력 임시값 사용

        # DB에서 설정된 임계값 로드
        config = self.db_manager.get_config()
        charge_limit_soc = config[3] if config and len(config) > 3 else 95.0
        low_voltage_threshold = config[2] if config and len(config) > 2 else 10.0

        # 2. 텍스트 위젯 업데이트 (UI 설계서 반영)
        self.lbl_batt_soc.setText(
            f"배터리 잔량: S1 {s1_v:.2f}V / S2 {s2_v:.2f}V / S3 {s3_v:.2f}V / Total {soc:.2f}%"
        )
        self.lbl_load_power.setText(f"부하 전력: 부하 전력: {load_power_v:.2f} V")

        # 3. 그래프 데이터 갱신
        self.data_count += 1  # X축 인덱스 증가 (분 단위 시뮬레이션 시간)
        self.time_data.append(self.data_count)
        self.pv_power_data.append(pv_power)

        # 최근 50개 데이터만 표시하도록 제어 (스크롤 효과)
        max_points = 50
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.pv_power_data = self.pv_power_data[-max_points:]

        self.curve.setData(self.time_data, self.pv_power_data)

        # 4. 경고 메시지 업데이트
        warning_text = "경고 메시지: 시스템 정상"
        warning_color = "color: black;"

        # A. 과충전 경고 체크
        if soc >= charge_limit_soc:
            warning_text = f"경고 메시지: 🚨 배터리 과충전 상태 ({soc:.2f}%)"
            warning_color = "color: #FF8C00; font-weight: bold;"

            # B. 저전압 경고 체크
        elif total_v < low_voltage_threshold:
            warning_text = f"경고 메시지: ⚠️ 배터리 저전압 기준 이하! ({total_v:.2f}V)"
            warning_color = "color: red; font-weight: bold;"

        self.lbl_warning_msg.setText(warning_text)
        self.lbl_warning_msg.setStyleSheet(warning_color)

    def _update_connection_status(self, is_connected):
        """연결 상태 시그널을 받아 UI의 연결 상태 라벨을 업데이트합니다."""
        status_text = "정상" if is_connected else "끊김"
        self.lbl_connection_status.setText(f"연결 상태: {status_text}")

    def closeEvent(self, event):
        """프로그램 종료 이벤트 발생 시, 스레드와 DB 연결을 안전하게 정리합니다."""
        print("프로그램 종료 중...")

        # 스레드 종료 및 DB/시리얼 연결 해제
        if hasattr(self, 'data_collector_thread') and self.data_collector_thread.isRunning():
            self.data_collector_thread.stop()

        self.db_manager.close()
        self.serial_manager.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EnergyPlatformApp()
    window.show()
    sys.exit(app.exec_())