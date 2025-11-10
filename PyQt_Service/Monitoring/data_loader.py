import pandas as pd

class DataLoader:
    """
    CSV 로드 + Date, Time 결합 -> timestamp 컬럼 생성
    컬럼 스키마 자동 감지 (battery / solar)
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self):
        # 인코딩 자동 처리
        for enc in ("utf-8-sig", "cp949", "utf-8"):
            try:
                df = pd.read_csv(self.file_path, encoding=enc)
                break
            except Exception:
                df = None
        if df is None:
            raise RuntimeError(f"CSV를 읽을 수 없습니다: {self.file_path}")

        # Date + Time -> timestamp
        if "Date" in df.columns and "Time" in df.columns:
            ts = (df["Date"].astype(str).str.strip() + " " + df["Time"].astype(str).str.strip())
            df["timestamp"] = pd.to_datetime(ts, errors="coerce")
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        else:
            raise ValueError("CSV에 Date/Time 또는 timestamp 컬럼이 필요합니다.")

        df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

        # 숫자 컬럼 안전 변환
        for col in df.columns:
            if col not in ("Date", "Time", "timestamp"):
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 스키마 태그
        schema = self._detect_schema(df)
        df.attrs["schema"] = schema
        return df

    def _detect_schema(self, df: pd.DataFrame) -> str:
        """
        battery: 1S Voltage, 2S Voltage, 3S Voltage, Total Voltage
        solar  : 전압(V), 전류(A), 전력량(W), 누적 전력량(Wh)
        """
        battery_keys = {"1S Voltage", "2S Voltage", "3S Voltage", "Total Voltage"}
        solar_keys = {"전압(V)", "전류(A)", "전력량(W)", "누적 전력량(Wh)"}

        if battery_keys.issubset(set(df.columns)):
            return "battery"
        if solar_keys.issubset(set(df.columns)):
            return "solar"
        # 모호한 경우, 포함수 많은 쪽
        b_score = len(battery_keys.intersection(df.columns))
        s_score = len(solar_keys.intersection(df.columns))
        return "battery" if b_score >= s_score else "solar"
