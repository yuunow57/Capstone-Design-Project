from PyQt5 import QtWidgets
import pandas as pd

class CSVExporter:
    """표 형태로 24시간(1분 주기 기준) 원본에 가까운 데이터 표시"""
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def show_table(self):
        if self.df.empty:
            return

        # 최근 24시간, 1분 리샘플
        end = self.df["timestamp"].max()
        start = end - pd.Timedelta(hours=24)
        scope = self.df[self.df["timestamp"].between(start, end)].copy()
        scope = scope.set_index("timestamp").resample("1T").mean().reset_index()

        dlg = QtWidgets.QDialog()
        dlg.setWindowTitle("24시간 기록 데이터 (1분 주기)")
        layout = QtWidgets.QVBoxLayout(dlg)
        table = QtWidgets.QTableWidget()
        layout.addWidget(table)

        cols = list(scope.columns)
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.setRowCount(len(scope))

        for i, row in scope.iterrows():
            for j, col in enumerate(cols):
                table.setItem(i, j, QtWidgets.QTableWidgetItem(str(row[col])))

        table.resizeColumnsToContents()
        dlg.resize(1000, 600)
        dlg.exec_()
