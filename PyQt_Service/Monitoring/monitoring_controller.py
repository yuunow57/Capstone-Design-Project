from .view_manager import ViewManager
from .data_loader import DataLoader

class MonitoringController:
    """
    Controller: UI와 매니저들을 '묶어' 주는 허브
    (SettingController와 동일한 역할)
    """
    def __init__(self, ui, csv_path: str):
        self.ui = ui
        self.csv_path = csv_path

        # 데이터 로드
        self.df = DataLoader(self.csv_path).load()

        # 뷰 매니저(로직 담당) 연결
        self.view_manager = ViewManager(self.ui, self.df)
