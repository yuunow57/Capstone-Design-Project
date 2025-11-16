from datetime import datetime


class LogService:
    _instance = None

    def __new__(cls):
        # 싱글톤 — 모든 컨트롤러가 같은 인스턴스를 공유
        if cls._instance is None:
            cls._instance = super(LogService, cls).__new__(cls)
            cls._instance.logs = []
        return cls._instance

    # ------------------------------------------------------
    # 로그 추가
    # ------------------------------------------------------
    def add(self, message: str):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{time}] {message}")
        print("📘 LOG:", self.logs[-1])   # 콘솔에도 출력

    # ------------------------------------------------------
    # 로그 전체 반환 (문자열)
    # ------------------------------------------------------
    def get_all(self) -> str:
        return "\n".join(self.logs)

    # ------------------------------------------------------
    # 로그 삭제
    # ------------------------------------------------------
    def clear(self):
        self.logs = []
