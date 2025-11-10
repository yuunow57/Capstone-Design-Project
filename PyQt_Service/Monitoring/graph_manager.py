import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphManager(FigureCanvas):
    """
    - 그래프 제목 제거 (GUI 쪽 라벨 사용)
    - 색상은 호출 시 전달받아 적용
    - 한글 폰트 경고 제거
    - 배경 투명, 그리드/테두리 정리
    """
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        super().__init__(self.fig)
        if parent is not None:
            self.setParent(parent)

        # 한글 폰트 경고 제거 (Windows: 맑은 고딕)
        plt.rcParams["font.family"] = "Malgun Gothic"
        plt.rcParams["axes.unicode_minus"] = False

        # 배경/레이아웃
        self.fig.patch.set_alpha(0)
        self.ax.set_facecolor("none")
        self.fig.tight_layout(pad=0)

    def update_graph(self, df, y_col, color_hex):
        """df에서 y_col을 그린다. 제목 없음."""
        self.ax.clear()

        if df is not None and (not df.empty) and (y_col in df.columns):
            self.ax.plot(df["timestamp"], df[y_col], linewidth=2, color=color_hex)

        # 축/눈금/그리드
        self.ax.tick_params(axis="x", labelrotation=30)
        self.ax.grid(True, linestyle="--", alpha=0.3)

        # 테두리 얇게
        for spine in self.ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_alpha(0.6)

        self.draw()
