import pandas as pd
from datetime import timedelta

class DataResampler:
    """
    주기 리샘플 + 기간 윈도우 자르기
    - '1분'  : 최근 3시간, 1T
    - '10분' : 최근 6시간, 10T
    - '1시간': 최근 24시간, 1H
    - '24시간': 최근 24시간, 1H (하루를 시간 단위로 보고)
    """

    RULE = {
        "1분":  ("1T", timedelta(hours=3)),
        "10분": ("10T", timedelta(hours=6)),
        "1시간": ("1H", timedelta(hours=24)),
        "24시간": ("1H", timedelta(hours=24)),  # 하루를 시간 단위로
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def resample(self, period: str) -> pd.DataFrame:
        rule, window = self.RULE.get(period, ("1T", timedelta(hours=3)))
        if self.df.empty:
            return self.df

        end = self.df["timestamp"].max()
        start = end - window
        scope = self.df[self.df["timestamp"].between(start, end)].copy()

        if scope.empty:
            return scope

        scope = scope.set_index("timestamp").resample(rule).mean().reset_index()
        return scope
