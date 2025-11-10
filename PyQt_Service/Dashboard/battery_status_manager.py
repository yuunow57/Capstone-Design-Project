import pandas as pd, os

class BatteryStatusManager:
    """3개 배터리 모듈의 충전 상태 표시 (샘플 CSV 기반)"""
    def __init__(self, label_widget, csv_path):
        self.label = label_widget
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_path, "../Monitoring/sample/battery_data.csv")
        self.df = pd.read_csv(self.csv_path, encoding="cp949")

    def update_status(self):
        if not self.label or self.df.empty:
            return
        latest = self.df.iloc[-1]
        v1, v2, v3 = latest["1S Voltage"], latest["2S Voltage"], latest["3S Voltage"]

        def calc_soc(v):
            return min(max((v - 2.5) / (4.2 - 2.5) * 100, 0), 100)

        s1, s2, s3 = map(calc_soc, [v1, v2, v3])
        text = f"1S: {s1:.1f}% / 2S: {s2:.1f}% / 3S: {s3:.1f}%"
        self.label.setText(f"<b>배터리 잔량</b>: {text}")
