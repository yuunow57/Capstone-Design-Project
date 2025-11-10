class ConnectionStatusManager:
    """연결 상태 표시"""
    def __init__(self, label_widget):
        self.label = label_widget
        self.connected = True

    def update_status(self):
        if not self.label:
            return
        status = "정상" if self.connected else "끊김"
        color = "#0014a9" if self.connected else "#a90000"
        self.label.setText(f"<b>연결 상태:</b> <span style='color:{color}'>{status}</span>")
