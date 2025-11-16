class LogManager:
    _instance = None

    def __init__(self):
        # 나중에 LogController가 여기로 등록됨
        self.controller = None

    @staticmethod
    def instance():
        if LogManager._instance is None:
            LogManager._instance = LogManager()
        return LogManager._instance

    def set_controller(self, controller):
        """로그 페이지 컨트롤러 등록"""
        self.controller = controller

    def log(self, msg: str):
        """터미널 + UI 로그 동시에 출력"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{now}] {msg}"

        # 1) 터미널 출력
        print("📘 LOG:", full_msg)

        # 2) UI 로그 출력
        if self.controller is None:
            print("⚠️ LogManager: controller is None, UI log skipped")
            return

        try:
            print("✅ LogManager: forwarding log to UI")
            self.controller.add_log(full_msg)
        except Exception as e:
            print("❌ LogManager: failed to write to UI:", e)
