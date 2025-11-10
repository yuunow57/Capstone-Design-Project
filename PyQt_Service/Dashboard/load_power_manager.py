import pandas as pd, os

class LoadPowerManager:
    """태양광 CSV 기반 부하 전력 표시"""
    def __init__(self, label_widget, csv_path):
        self.label = label_widget
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_path, "../Monitoring/sample/solar_data.csv")
        self.df = pd.read_csv(self.csv_path, encoding="cp949")

    def update_value(self):
        if not self.label or self.df.empty:
            return
        latest = self.df.iloc[-1]
        power = latest["전력량(W)"]
        self.label.setText(f"<b style='font-size:14pt;'>부하 전력: </b> <span style='font-size:14pt;'>{power:.2f} W</span>")
