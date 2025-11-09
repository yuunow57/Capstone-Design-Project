import time
from PyQt5.QtCore import QThread, pyqtSignal
from serial_manager import SerialManager
from db_manager import DatabaseManager


class DataCollector(QThread):
    """
    백그라운드에서 데이터를 수집하고 처리하는 QThread 클래스.
    - 메인 GUI가 멈추지 않도록 데이터 통신 및 DB 작업을 분리합니다.
    - 데이터 시그널을 통해 수집된 최신 데이터를 GUI로 실시간 전송합니다.
    """

    # PyQt Signal 정의: 수집된 최신 데이터를 dict 형태로 메인 UI에 전송
    data_received = pyqtSignal(dict)
    # 통신 연결 상태를 bool 형태로 메인 UI에 전송
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, db_manager, serial_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager  # DatabaseManager 인스턴스
        self.sm = serial_manager  # SerialManager 인스턴스 (CSV 시뮬레이션 담당)
        self._is_running = True  # 스레드 실행 플래그
        self._refresh_rate_ms = 2000  # 데이터 갱신 주기 (기본 2000ms, DB에서 로드됨)

    def stop(self):
        """스레드를 안전하게 종료합니다."""
        self._is_running = False
        self.wait()  # 스레드가 완전히 종료될 때까지 대기

    def set_refresh_rate(self, ms):
        """시스템 설정값(갱신 주기)을 업데이트합니다."""
        self._refresh_rate_ms = ms

    def run(self):
        """스레드의 메인 루프: 데이터 수집, 처리, 저장, 제어 로직 실행"""

        # 1. 초기 통신 연결 시도
        if not self.sm.is_connected:
            self.sm._connect()
            self.connection_status_changed.emit(self.sm.is_connected)

        while self._is_running:
            start_time = time.time()

            if not self.sm.is_connected:
                time.sleep(1)
                continue

            # 2. 데이터 요청 및 수신 (CSV 파일에서 다음 샘플 읽기)
            raw_data = self.sm.request_data()

            if raw_data:
                # 3. 데이터 처리 및 DB 저장

                # 'TOTAL_VOLTAGE'를 이용해 SOC (총 충전율) 계산
                total_v = raw_data.get('TOTAL_VOLTAGE', 0)
                soc = self._calculate_soc(total_v)
                raw_data['SOC_TOTAL'] = soc  # 계산된 SOC를 딕셔너리에 추가

                # DB 삽입을 위한 데이터 튜플 생성 (기술서의 measurement 테이블 컬럼 순서에 맞춤)
                db_data = (
                    raw_data.get('PV_VOLTAGE'), raw_data.get('PV_CURRENT'), raw_data.get('PV_POWER'),
                    raw_data.get('BATT1_VOLTAGE'), raw_data.get('BATT2_VOLTAGE'), raw_data.get('BATT3_VOLTAGE'),
                    raw_data.get('TOTAL_VOLTAGE'), raw_data.get('MAX_CURRENT'), raw_data.get('ENERGY_WH'),
                    raw_data.get('TEMPERATURE'), raw_data.get('SOC_TOTAL'), raw_data.get('CHARGE_STAGE')
                )

                # 측정 데이터 DB 저장 및 생성된 ID 반환 (FK 연결을 위해 필요)
                measurement_id = self.db.insert_measurement(db_data)

                # 4. 자동 제어 로직 실행 및 기록
                self._run_auto_control(raw_data, measurement_id)

                # 5. GUI 업데이트를 위해 시그널 전송
                self.data_received.emit(raw_data)

            # 6. 주기 제어: 설정된 갱신 주기(ms)를 맞추기 위한 딜레이 계산
            elapsed_time_ms = (time.time() - start_time) * 1000
            sleep_time_s = max(0, (self._refresh_rate_ms - elapsed_time_ms) / 1000.0)
            time.sleep(sleep_time_s)

    def _calculate_soc(self, total_voltage):
        """전압을 기반으로 SOC(총 충전율)를 계산하는 임시 함수 (3S 팩 기준)"""
        # [기술적 가정] Low cut-off (0%): 8.0V / Fully charged (100%): 12.6V
        V_min = 8.0
        V_max = 12.6
        soc_percentage = ((total_voltage - V_min) / (V_max - V_min)) * 100

        # SOC를 0% ~ 100% 범위로 제한
        return max(0, min(100, round(soc_percentage, 2)))

    def _run_auto_control(self, data, measurement_id):
        """
        에너지 관리 자동 제어 로직: PV 발전 여부와 배터리 잔량에 따라 시스템을 제어합니다.
        제어 동작 발생 시 realy_log 테이블에 기록합니다.
        """
        # DB에서 현재 설정된 저전압 기준(LOW_VOLTAGE) 값을 로드
        config = self.db.get_config()
        low_voltage_threshold = config[2] if config and len(config) > 2 else 10.0  # 기본값 10.0V

        pv_v = data.get('PV_VOLTAGE', 0)
        total_v = data.get('TOTAL_VOLTAGE', 0)

        # PV 발전 상태 및 배터리 잔량 상태 판단
        is_pv_ok = pv_v >= 5.0  # 태양광 발전 기준 (임시 5.0V)
        is_batt_ok = total_v >= low_voltage_threshold  # 배터리가 저전압 기준 이상인지

        action = None
        reason = "No change"

        # ⭐️ 4가지 시나리오 기반 제어 로직

        # 시나리오 1: 태양광 O & 잔량 부족 (기준전압 이하)
        if is_pv_ok and not is_batt_ok:
            action = 'CHRG_ON + LOAD_COM'
            reason = "PV ON, Battery LOW. Charge Battery, Use Commercial Power."
            # 충전 릴레이 ON (채널 2 가정)
            self.db.insert_realy_log(measurement_id, channel_no=2, state='ON', reason=reason)

        # 시나리오 2: 태양광 O & 잔량 충분 (기준전압 이상)
        elif is_pv_ok and is_batt_ok:
            action = 'LOAD_PV'
            reason = "PV ON, Battery OK. Use PV Power for Load."
            # 충전 릴레이 OFF
            self.db.insert_realy_log(measurement_id, channel_no=2, state='OFF', reason=reason)

        # 시나리오 3: 태양광 X & 잔량 부족
        elif not is_pv_ok and not is_batt_ok:
            action = 'LOAD_COM'
            reason = "PV OFF, Battery LOW. Use Commercial Power for Load."
            # 충전 릴레이 OFF
            self.db.insert_realy_log(measurement_id, channel_no=2, state='OFF', reason=reason)

        # 시나리오 4: 태양광 X & 잔량 충분
        elif not is_pv_ok and is_batt_ok:
            action = 'LOAD_BATT'
            reason = "PV OFF, Battery OK. Use Battery Power for Load."
            # 충전 릴레이 OFF
            self.db.insert_realy_log(measurement_id, channel_no=2, state='OFF', reason=reason)

        return action