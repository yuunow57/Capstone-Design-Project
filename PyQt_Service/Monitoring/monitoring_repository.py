import pandas as pd
from PyQt_Service.Database.db import db

class MonitoringRepository:
    
    def fetch_last_n_rows(self, limit: int):
        """
        measurement 테이블에서 가장 마지막 N개의 row 가져오기
        """
        sql = f"""
            SELECT *
            FROM measurement
            ORDER BY ts DESC
            LIMIT {limit}
        """
        try:
            conn = db.conn
            df = pd.read_sql(sql, conn)

            if df.empty:
                return df

            # 오래된 → 최신 순으로 다시 정렬
            df = df.sort_values("ts", ascending=True)

            # ts datetime 변환
            df["ts"] = pd.to_datetime(df["ts"])
            return df

        except Exception as e:
            print("⚠️ fetch_last_n_rows() SQL ERROR:", e)
            return pd.DataFrame()

    def get_latest_measurement(self):
        sql = """
            SELECT *
            FROM measurement
            ORDER BY ts DESC
            LIMIT 1
        """
        try:
            conn = db.conn
            df = pd.read_sql(sql, conn)

            if df.empty:
                return None
            
            df["ts"] = pd.to_datetime(df["ts"])
            return df.iloc[0]

        except Exception as e:
            print("⚠️ get_latest_measurement() SQL ERROR:", e)
            return None
