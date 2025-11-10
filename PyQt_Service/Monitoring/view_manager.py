from PyQt5 import QtWidgets
from .graph_manager import GraphManager
from .data_resampler import DataResampler
from .csv_exporter import CSVExporter

class ViewManager:
    """
    이벤트 처리 + 그래프 갱신 로직 담당
    (Setting 패턴의 '로직 담당자')
    """
    def __init__(self, ui, df):
        self.ui = ui
        self.df = df
        self.schema = df.attrs.get("schema", "battery")

        # 그래프 4개 생성 및 프레임에 삽입 (F_1~F_4)
        titles, ylabels = self._graph_titles_and_labels()
        self.graphs = [
            GraphManager(title=titles[0], ylabel=ylabels[0]),
            GraphManager(title=titles[1], ylabel=ylabels[1]),
            GraphManager(title=titles[2], ylabel=ylabels[2]),
            GraphManager(title=titles[3], ylabel=ylabels[3]),
        ]
        frames = [self.ui.frame, self.ui.frame_3, self.ui.frame_2, self.ui.frame_4]
        for fr, g in zip(frames, self.graphs):
            lay = QtWidgets.QVBoxLayout(fr)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(g)

        # 이벤트 연결
        self.ui.comboBox_interval.currentTextChanged.connect(self.update_graphs)
        self.ui.btn_show_csv.clicked.connect(self.show_csv)

        # 초기 렌더
        self.update_graphs()

    def _graph_titles_and_labels(self):
        """
        battery: 1S Voltage, 2S Voltage, 3S Voltage, Total Voltage
        solar  : 전압(V), 전류(A), 전력량(W), 누적 전력량(Wh)
        """
        if self.schema == "battery":
            return (["1S Voltage", "2S Voltage", "3S Voltage", "Total Voltage"],
                    ["전압(V)"]*4)
        else:
            return (["전압(V)", "전류(A)", "전력량(W)", "누적 전력량(Wh)"],
                    ["전압(V)", "전류(A)", "전력(W)", "에너지(Wh)"])

    def _y_columns(self):
        return self._graph_titles_and_labels()[0]

    def update_graphs(self):
        period = self.ui.comboBox_interval.currentText()
        res = DataResampler(self.df).resample(period)
        ycols = self._y_columns()
        for g, y in zip(self.graphs, ycols):
            g.update_graph(res, y_col=y, title=y)

    def show_csv(self):
        CSVExporter(self.df).show_table()
