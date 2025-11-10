import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphManager(FigureCanvas):
    """단일 그래프 캔버스 (Matplotlib)"""
    def __init__(self, title="Graph", ylabel=""):
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        super().__init__(self.fig)
        self.ax.set_title(title)
        self.ax.set_xlabel("시간")
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True)

    def update_graph(self, df, y_col, title=None, ylabel=None):
        self.ax.clear()
        if title:
            self.ax.set_title(title)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        self.ax.set_xlabel("시간")
        self.ax.grid(True)

        if df is not None and (y_col in df.columns):
            self.ax.plot(df["timestamp"], df[y_col])
            self.fig.autofmt_xdate()

        self.draw()
