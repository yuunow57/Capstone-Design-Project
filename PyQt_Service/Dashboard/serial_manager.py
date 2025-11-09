import pandas as pd
import time
import os
import itertools


# import serial # 실제 직렬 통신(하드웨어 연결) 시에만 필요합니다.

class SerialManager:
    """
    VC_MON_LC 모듈과의 직렬 통신을 대신하여 CSV 파일을 이용한 데이터 시뮬레이션을 담당하는 클래스입니다.
    데이터 수집 스레드(collector_thread)에 주기적으로 샘플 데이터를 제공합니다.
    """

    def __init__(self, port_name=None, solar_file='data sample_solar3.csv', batt_file='data sample_battery.csv'):

        # 1. CSV 데이터 로드 및 초기화
        # PV(태양광) 데이터 파일 로드
        self.solar_data = self._load_data(solar_file)
        # BATT(배터리) 데이터 파일 로드
        self.batt_data = self._load_data(batt_file)

        # itertools.cycle을 사용하여 데이터가 끝까지 읽힌 후 처음부터 다시 반복되도록 설정 (무한 시뮬레이션)
        self.solar_iterator = itertools.cycle(self.solar_data.itertuples(index=False))
        self.batt_iterator = itertools.cycle(self.batt_data.itertuples(index=False))

        self.is_connected = False
        self.port_name = port_name  # 설정 화면에서 받은 포트명을 저장 (시뮬레이션에서는 사용하지 않음)
        print("데이터 시뮬레이션 모드 활성화.")

    def _load_data(self, file_name):
        """
        주어진 파일 이름의 CSV 파일을 로드합니다. (파일 경로 처리 및 인코딩 오류 방지)
        """
        # 현재 실행 경로를 기준으로 파일의 절대 경로를 생성
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"필수 데이터 파일이 없습니다: {file_name}")

        # 한글 인코딩 오류(cp949/utf-8) 방지 로직 적용
        try:
            return pd.read_csv(full_path, encoding='cp949')
        except UnicodeDecodeError:
            return pd.read_csv(full_path, encoding='utf-8')
        except Exception as e:
            raise Exception(f"CSV 파일 로드 중 알 수 없는 오류 발생: {e}")

    def _connect(self):
        """
        직렬 포트 연결을 시뮬레이션합니다. (실제 통신 시에는 serial.Serial.open() 역할을 대신함)
        """
        self.is_connected = True
        print("시뮬레이션 연결 성공: CSV 데이터 로드됨")
        return True

    def close(self):
        """시뮬레이션 연결 상태를 종료합니다. (실제 통신 시에는 serial.Serial.close() 역할을 대신함)"""
        self.is_connected = False
        print("시뮬레이션 연결 종료.")

    def request_data(self):
        """
        VC_MON_LC 모듈에 데이터 요청 명령을 시뮬레이션하고, CSV 파일에서 다음 샘플 데이터를 반환합니다.
        """
        if not self.is_connected:
            return None

        # 순환 반복자에서 다음 행(데이터 샘플)을 읽어옴 (이것이 실시간 통신 응답 데이터를 대체함)
        solar_row = next(self.solar_iterator)
        batt_row = next(self.batt_iterator)

        # 튜플 형태로 읽어온 데이터를 컬럼 순서에 맞게 딕셔너리로 변환
        # 인덱스 (_N)는 CSV 파일의 컬럼 순서에 따라 결정됨
        parsed_data = {
            # 태양광 데이터 (PV_VOLTAGE, PV_CURRENT 등)
            'PV_VOLTAGE': solar_row._2,
            'PV_CURRENT': solar_row._3,
            'PV_POWER': solar_row._4,
            'ENERGY_WH': solar_row._5,
            'MAX_CURRENT': 0.0,  # 샘플 데이터에 없으므로 0으로 가정

            # 배터리 셀 및 총 전압 데이터
            'BATT1_VOLTAGE': batt_row._2,
            'BATT2_VOLTAGE': batt_row._3,
            'BATT3_VOLTAGE': batt_row._4,
            'TOTAL_VOLTAGE': batt_row._5,

            # 기타 데이터 (임시값)
            'TEMPERATURE': 25.0,  # 고정된 임시 온도
            'SOC_TOTAL': 0.0,  # collector_thread에서 계산될 예정이므로 초기값 0
            'CHARGE_STAGE': 'Idle'
        }

        return parsed_data

    def parse_data(self, raw_data):
        """
        (시뮬레이션 모드에서는 사용되지 않음) 실제 통신 시 수신된 raw 문자열을 파싱하는 함수를 가정합니다.
        """
        return raw_data