from PyQt5 import QtWidgets
from PyQt_Service.Monitoring.data_loader import DataLoader
from PyQt_Service.Monitoring.data_resampler import DataResampler
from PyQt_Service.Monitoring.graph_manager import GraphManager


class DashboardController:
    """
    대시보드 미니그래프 관리 컨트롤러
    (Monitoring 모듈의 그래프 로직을 재활용)
    """
    def __init__(self, ui, csv_path):
        self.ui = ui
        self.csv_path = csv_path
        self.df = DataLoader(csv_path).load()

        self.init_graph()

    def init_graph(self):
        print("🎨 대시보드 그래프 초기화 시작")

        if not hasattr(self.ui, "widget_graph_area"):
            print("❌ widget_graph_area 속성이 없습니다!")
            return

        layout = QtWidgets.QVBoxLayout(self.ui.widget_graph_area)
        layout.setContentsMargins(0, 0, 0, 0)
        self.graph = GraphManager(self.ui.widget_graph_area)
        layout.addWidget(self.graph)

        self.update_graph()

    def update_graph(self):
        res = DataResampler(self.df).resample("1시간")  # 1시간 주기 리샘플
        if res.empty:
            print("⚠️ 데이터프레임이 비어있습니다.")
            return

        # ✅ CSV 실제 컬럼명 → 표준 이름으로 매핑
        res = res.rename(columns={
            "일시": "timestamp",
            "전압(V)": "전압",
            "전류(A)": "전류",
            "출력(W)": "전력량"
        })

        # ✅ 필요한 컬럼만 선택 (존재하는지 확인 후)
        required_cols = ["timestamp", "전압", "전류", "전력량"]
        missing = [col for col in required_cols if col not in res.columns]
        if missing:
            print(f"⚠️ 누락된 컬럼: {missing}")
            return

        filtered = res[required_cols]

        # ✅ 그래프 초기화 및 스타일 설정
        self.graph.ax.clear()
        self.graph.ax.plot(filtered["timestamp"], filtered["전압"], color="#930B0D")
        self.graph.ax.plot(filtered["timestamp"], filtered["전류"], color="#0C6AA4")
        self.graph.ax.plot(filtered["timestamp"], filtered["전력량"], color="#4C934C")

        # ✅ Y축: 0부터 시작, 정수 단위 눈금 설정
        self.graph.ax.set_ylim(bottom=0)
        self.graph.ax.yaxis.get_major_locator().set_params(integer=True)

        # ✅ X축 표시 형식 (시간만)
        import matplotlib.dates as mdates
        self.graph.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

        self.graph.ax.tick_params(axis="x", labelrotation=30)
        self.graph.ax.grid(True, linestyle="--", alpha=0.3)
        self.graph.ax.legend(fontsize=8, loc="upper right")

        self.graph.draw()

