import pandas as pd
from datetime import timedelta

class DataResampler:
    """
    주기 리샘플 + 기간 윈도우 자르기
    - '1분'  : 최근 3시간, 1T
    - '10분' : 최근 6시간, 10T
    - '1시간': 최근 24시간, 1H
    - '24시간': 최근 7일, 1H (하루를 시간 단위로 보고)
    """

    RULE = {
        "1분":  ("1min", timedelta(hours=3)),
        "10분": ("10T", timedelta(hours=6)),
        "1시간": ("1H", timedelta(hours=24)),
        "24시간": ("1H", timedelta(days=7)),  # 하루를 시간 단위로
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def resample(self, period: str) -> pd.DataFrame:
        rule, window = self.RULE.get(period, ("1min", timedelta(hours=3)))
        if self.df.empty:
            return self.df

        # ✅ timestamp 문자열을 datetime으로 변환 (핵심 수정)
        if not pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], errors="coerce")

        # ✅ 변환 후 NaT 제거 (datetime 변환 실패한 행 제거)
        self.df = self.df.dropna(subset=["timestamp"])

        # ✅ 기간 윈도우 계산
        end = self.df["timestamp"].max()
        start = end - window
        scope = self.df[self.df["timestamp"].between(start, end)].copy()

        if scope.empty:
            return scope

        # ✅ 리샘플링 (시간 인덱스로 변환 후 평균)
        scope = scope.set_index("timestamp").resample(rule).mean(numeric_only=True).reset_index()

        return scope
