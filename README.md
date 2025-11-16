# 캡스톤 디자인: 🔅태양광-이차전지 연계형 에너지 관리 플랫폼

## 의존성 설치
```
pip install PyQt5 pandas matplotlib pyserial pyqtgraph mysql-connector-python
```



## 📁 폴더 구조  
```
📦 Capstone_Design_Project
│
├─ 📂 PyQt_GUI                          # 전체 GUI 화면 관리
│   ├─ 📜 stack.py                         # 페이지 전환 및 앱 실행 메인 파일
│   ├─ 📜 dashboard.ui                     # 대시보드 UI
│   ├─ 📜 sungp.ui                         # 태양광 모니터링 UI
│   ├─ 📜 log.ui                           # 시스템 로그 UI
│   ├─ 📜 new_set.ui                       # 설정 페이지 UI
│   └─ 📜 information.ui                   # 시스템 정보 UI
│
└─ 📂 PyQt_Service                      # 각 기능 로직을 모듈화한 서비스 계층
    │
    ├─ 📂 Dashboard                     # 대시보드 기능 로직
    │   ├─ 📜 dashboard_controller.py      # 대시보드 UI 업데이트·이벤트 제어
    │   └─ 📜 dashboard_service.py         # 배터리·태양광 데이터 가공 서비스
    │
    ├─ 📂 Database                      # 데이터베이스 관리 계층
    │   ├─ 📜 db.py                        # MySQL 연결 및 커넥션 관리
    │   ├─ 📜 create_table_measurement.sql # measurement 테이블 생성 SQL
    │   └─ 📜 insert_dummy_measurement.py  # 더미 데이터 삽입 스크립트
    │
    ├─ 📂 Log                           # 시스템 로그 관리
    │   ├─ 📜 log_controller.py            # 로그 UI 제어
    │   ├─ 📜 log_manager.py               # 싱글톤 기반 로그 관리
    │   └─ 📜 log_service.py               # 로그 저장·정리 서비스
    │
    ├─ 📂 Monitoring                    # 실시간 태양광/전력 데이터 모니터링
    │   ├─ 📜 monitoring_controller.py     # 모니터링 UI & 그래프 통합 제어
    │   ├─ 📜 monitoring_service.py        # 주기별 데이터 리샘플링·반환 서비스
    │   ├─ 📜 monitoring_repository.py     # DB에서 데이터 조회
    │   ├─ 📜 monitoring_collector.py      # 하드웨어 데이터 수집(1분 주기)
    │   └─ 📜 serial_manager.py            # 시리얼 통신 관리
    │
    └─ 📂 Setting                       # 설정 페이지 기능
        ├─ 📜 setting_controller.py        # 설정 UI 중앙 제어(포트·버튼 이벤트)
        ├─ 📜 command_service.py           # 아두이노 명령 송신($a ~ $v)
        ├─ 📜 serial_manager.py            # USB 포트 탐색·연결·해제
        ├─ 📜 device_state.py              # 시스템 장치 상태 저장
        └─ 📜 config_apply_manager.py      # 설정값 저장 및 적용(옵션)
```



