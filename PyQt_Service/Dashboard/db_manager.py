import sqlite3
import os
import time


class DatabaseManager:
    """
    SQLite 데이터베이스의 연결, 생성, 기본 설정을 관리하는 클래스입니다.
    이 클래스는 Measurement, realy_log, system_config 테이블을 정의합니다.
    """

    def __init__(self, db_name='energy_platform.db'):
        # DB 파일 경로 설정 (프로젝트 폴더 내에 생성)
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.conn = None
        self.cursor = None

        # DB 연결 및 테이블 생성 프로세스 시작
        self._connect()
        self._create_tables()

    def _connect(self):
        """데이터베이스에 연결을 시도하고 성공/실패 여부를 출력합니다."""
        try:
            # check_same_thread=False: 멀티스레드 환경(QThread)에서 안전하게 DB를 사용하도록 설정
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"데이터베이스 연결 성공: {self.db_path}")
        except sqlite3.Error as e:
            print(f"데이터베이스 연결 오류: {e}")

    def close(self):
        """데이터베이스 연결을 닫고 자원을 해제합니다."""
        if self.conn:
            self.conn.close()
            print("데이터베이스 연결 종료.")

    def _create_tables(self):
        """프로젝트 기술서에 정의된 3개의 테이블(측정값, 동작 기록, 설정)을 생성합니다."""

        # 1. 측정값 테이블 (Measurement) 정의: 센서에서 수집되는 모든 실시간 데이터 저장
        # 기술서에 따라 3S 셀 전압 및 CONFIG_ID 외래 키 포함
        measurement_table = """
                            CREATE TABLE IF NOT EXISTS measurement (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                CONFIG_ID TINYINT NOT NULL, 
                                TIMESTAMP DATETIEM NOT NULL,
                                PV_VOLTAGE DECIMAL(10,3),
                                PV_CURRENT DECIMAL(10,3),
                                PV_POWER DECIMAL(12,3),
                                BATT1_VOLTAGE DECIMAL(10,3),
                                BATT2_VOLTAGE DECIMAL(10,3),
                                BATT3_VOLTAGE DECIMAL(10,3),
                                TOTAL_VOLTAGE DECIMAL(10,3),
                                MAX_CURRENT DECIMAL(10,3),
                                ENERGY_WH DECIMAL(14,3),
                                TEMPERATURE DECIMAL(7,3),
                                SOC_TOTAL DECIMAL(6,3),
                                CHARGE_STAGE VARCHAR(20),
                                FOREIGN KEY(CONFIG_ID) REFERENCES system_config(ID)
                            );
                            """

        # 2. 동작 기록 테이블 (Realy_log) 정의: 릴레이 제어 이력 및 사유 저장
        # 기술서에 따라 MEASUREMENT_ID 외래 키 포함
        realy_log_table = """
                          CREATE TABLE IF NOT EXISTS realy_log (
                              ID INTEGER PRIMARY KEY AUTOINCREMENT,
                              MEASUREMENT_ID BIGINT NOT NULL,
                              TIMESTAMP DATETIEM NOT NULL,
                              CHANNEL_NO TINYINT NOT NULL,
                              STATE VARCHAR(10) NOT NULL,
                              REASON VARCHAR(100),
                              FOREIGN KEY(MEASUREMENT_ID) REFERENCES measurement(ID)
                          );
                          """

        # 3. 시스템 설정 테이블 (System_config) 정의: 관제 시스템의 운영 기준 저장
        config_table = """
                       CREATE TABLE IF NOT EXISTS system_config (
                           ID INTEGER PRIMARY KEY,
                           DATA_REFRESH_MS INT,
                           LOW_VOLTAGE DECIMAL(10,3),
                           CHARGE_LIMIT_SOC DECIMAL(5,2),
                           PORT_NAME VARCHAR(40),
                           UPDATED_AT TIMESTAMP
                           );
                       """

        try:
            # 외래 키(FK) 제약 조건을 활성화합니다.
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            # 테이블 생성
            self.cursor.execute(config_table)
            self.cursor.execute(measurement_table)
            self.cursor.execute(realy_log_table)
            self.conn.commit()
            # 기본 설정값 삽입 함수 호출
            self._insert_default_config()
        except sqlite3.Error as e:
            print(f"테이블 생성 오류: {e}")

    def _insert_default_config(self):
        """system_config 테이블에 기본 설정값이 없을 경우, 초기값을 삽입합니다."""
        self.cursor.execute("SELECT COUNT(*) FROM system_config WHERE ID = 1")
        if self.cursor.fetchone()[0] == 0:
            # 기본값 (갱신 주기 2000ms, 저전압 기준 10.0V, 충전 한계 95.0%, 포트명 'COM3')
            default_query = """
                            INSERT INTO system_config (ID, DATA_REFRESH_MS, LOW_VOLTAGE, CHARGE_LIMIT_SOC, PORT_NAME, 
                                                       UPDATED_AT)
                            VALUES (1, 2000, 10.0, 95.0, 'COM3', DATETIME('now'))
                            """
            self.cursor.execute(default_query)
            self.conn.commit()
            print("기본 설정값 삽입 완료.")

    def get_config(self):
        """현재 운영 설정(ID=1)을 조회하여 튜플 형태로 반환합니다. (갱신 주기, 저전압 기준 등)"""
        self.cursor.execute("SELECT * FROM system_config WHERE ID = 1")
        return self.cursor.fetchone()

    def insert_measurement(self, data):
        """
        새로운 측정 데이터를 measurement 테이블에 삽입합니다.
        성공 시, 새로 생성된 PRIMARY KEY(ID)를 반환합니다.
        """
        # CONFIG_ID는 기본 설정(1)로 고정
        query = """
                INSERT INTO measurement (CONFIG_ID, TIMESTAMP, PV_VOLTAGE, PV_CURRENT, PV_POWER,
                                         BATT1_VOLTAGE, BATT2_VOLTAGE, BATT3_VOLTAGE, TOTAL_VOLTAGE,
                                         MAX_CURRENT, ENERGY_WH, TEMPERATURE, SOC_TOTAL, CHARGE_STAGE)
                VALUES (1, DATETIME('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
        try:
            self.cursor.execute(query, data)
            self.conn.commit()
            return self.cursor.lastrowid  # realy_log의 FK로 사용될 ID 반환
        except sqlite3.Error as e:
            print(f"데이터 삽입 오류: {e}")
            return None

    def insert_realy_log(self, measurement_id, channel_no, state, reason):
        """
        릴레이 동작 기록(ON/OFF)을 realy_log 테이블에 삽입합니다.
        measurement_id를 외래 키로 연결하여 어떤 측정값 시점에 동작했는지 기록합니다.
        """
        query = """
                INSERT INTO realy_log (MEASUREMENT_ID, TIMESTAMP, CHANNEL_NO, STATE, REASON)
                VALUES (?, DATETIME('now'), ?, ?, ?)
                """
        try:
            self.cursor.execute(query, (measurement_id, channel_no, state, reason))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"릴레이 로그 삽입 오류: {e}")
            return False


# 간단한 테스트 (main.py에서 실행되므로 주석 처리 권장)
if __name__ == '__main__':
    db = DatabaseManager()
    db.close()