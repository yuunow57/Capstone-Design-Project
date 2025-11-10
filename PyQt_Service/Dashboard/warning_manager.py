class WarningManager:
    """경고 메시지 표시"""
    def __init__(self, label_widget):
        self.label = label_widget

    def update_message(self):
        if not self.label:
            return
        self.label.setText("<b>경고 메시지:</b> <span style='color:#00aa00'>정상</span>")
