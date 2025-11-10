# PyQt_Service/Monitoring/data_resampler.py
import pandas as pd
from datetime import timedelta

class DataResampler:
    """
    주기 리샘플 + 기간 윈도우 자르기
    - '1분'  : 최근 3시간, 1min
    - '10분' : 최근 6시간, 10T
    - '1시간': 최근 24시간, 1H
    - '24시간': 최근 7일, 24H (일 단위)
    """

    RULE = {
        "1분":  ("1T", timedelta(hours=3)),
        "10분": ("10T", timedelta(hours=6)),
        "1시간": ("1H", timedelta(hours=24)),
        "24시간": ("1H", timedelta(days=7)),  # ✅ 하루 단위로, 최근 7일만
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

        # ✅ Date + Time 자동 결합
        if "Date" in self.df.columns and "Time" in self.df.columns:
            self.df["timestamp"] = pd.to_datetime(
                self.df["Date"].astype(str) + " " + self.df["Time"].astype(str),
                errors="coerce"
            )
        elif "Date" in self.df.columns:
            self.df["timestamp"] = pd.to_datetime(self.df["Date"], errors="coerce")
        else:
            # 타임스탬프 직접 존재하는 경우
            if "timestamp" in self.df.columns:
                self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], errors="coerce")

        # ✅ NaT, 중복, 정렬 정리
        self.df = self.df.dropna(subset=["timestamp"]).drop_duplicates(subset=["timestamp"])
        self.df = self.df.sort_values("timestamp").reset_index(drop=True)

    def resample(self, period: str) -> pd.DataFrame:
        rule, window = self.RULE.get(period, ("1T", timedelta(hours=3)))

        if self.df.empty:
            print("⚠️ 데이터프레임이 비어있음.")
            return self.df

        # ✅ 최신 시점 기준 정확히 최근 window만 자르기
        end = pd.to_datetime(self.df["timestamp"].max())
        start = end - window

        # timestamp가 datetime64임을 보장
        if not pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], errors="coerce")

        # ✅ 필터 구간 확인
        scope = self.df[self.df["timestamp"].between(start, end)].copy()

        if scope.empty:
            print(f"⚠️ [{period}] 기간 내 데이터 없음: {start} ~ {end}")
            return scope

        # ✅ 리샘플 (숫자형 컬럼만 평균)
        scope = (
            scope.set_index("timestamp")
                 .resample(rule)
                 .mean(numeric_only=True)
                 .reset_index()
        )
        return scope
