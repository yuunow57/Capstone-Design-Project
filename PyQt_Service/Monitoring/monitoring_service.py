import pandas as pd
from PyQt_Service.Monitoring.monitoring_repository import MonitoringRepository
from PyQt_Service.Database.db import db

class MonitoringService:
    def __init__(self):
        self.repo = MonitoringRepository()

    def get_graph_data(self, mode):
        if mode == "1분":
            df = self.repo.fetch_last_n_rows(180)

        elif mode == "10분":
            df = self.repo.fetch_last_n_rows(360)
            df = df.groupby(df.index // 10).mean()

        elif mode == "1시간":
            df = self.repo.fetch_last_n_rows(1440)
            df = df.groupby(df.index // 60).mean()

        elif mode == "24시간":
            df = self.repo.fetch_last_n_rows(10080)
            df = df.groupby(df.index // 1440).mean()

        else:
            return pd.DataFrame()

        # ts 컬럼은 그룹화 후 의미가 없으므로 인덱스로 대체
        df.reset_index(drop=True, inplace=True)
        return df
    
    def get_raw_last_24h(self):
        sql = """
            SELECT *
            FROM measurement
            ORDER BY ts DESC
            LIMIT 1440;
        """
        try:
            conn = db.conn
            df = pd.read_sql(sql, conn)

            # 최신 → 오래된 순으로 정렬 (그래프/테이블 정상 표시)
            df = df.sort_values(by="ts", ascending=True).reset_index(drop=True)

            return df
        except Exception as e:
            print("⚠️ get_raw_last_24h() ERROR:", e)
            return None

