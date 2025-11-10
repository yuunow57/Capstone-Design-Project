import pandas as pd
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

class CSVExporter:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def show_table(self):
        if self.df.empty:
            print("⚠️ CSV 데이터가 비어 있습니다.")
            return

        # ✅ 숫자형 컬럼만 선택 (timestamp 제외)
        numeric_cols = self.df.select_dtypes(include=["number"]).columns
        cols_to_use = ["timestamp"] + list(numeric_cols)

        scope = self.df[cols_to_use].copy()
        scope["timestamp"] = pd.to_datetime(scope["timestamp"], errors="coerce")

        # ✅ timestamp를 인덱스로 리샘플링
        scope = scope.set_index("timestamp").resample("1T").mean(numeric_only=True).reset_index()

        # GUI 테이블로 표시
        dialog = QDialog()
        dialog.setWindowTitle("CSV 데이터 미리보기")

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        layout.addWidget(table)

        table.setColumnCount(len(scope.columns))
        table.setRowCount(len(scope))
        table.setHorizontalHeaderLabels(scope.columns)

        for i, row in enumerate(scope.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))

        dialog.resize(800, 600)
        dialog.exec_()
