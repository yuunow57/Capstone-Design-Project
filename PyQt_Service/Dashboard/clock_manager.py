from PyQt5.QtCore import QTime

class ClockManager:
    """현재 시각을 hh:mm:ss로 표시"""
    def __init__(self, label_widget):
        self.label = label_widget

    def update_time(self):
        if not self.label:
            return
        now = QTime.currentTime().toString("hh:mm:ss")
        self.label.setText(f"<b style='font-size:14pt;'>현재 시각: </b><span style='font-size:14pt; color:#00ac00;'>{now}</span>")
