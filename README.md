# 캡스톤 디자인: 🔅태양광-이차전지 연계형 에너지 관리 플랫폼

## 의존성 설치
```
pip install PyQt5 pandas matplotlib pyserial
```



## 📁 폴더 구조  
```
📦 Capstone_Design_Project  
┣ 📂 PyQt_GUI              # GUI 로직 관리
┃  ┣ 📜 stack.py                # GUI 실행 및 화면 전환 관리
┃  ┣ 📜 dashboard.ui            # 대시보드 UI
┃  ┣ 📜 sungp.ui                # 태양광 발전 현황 모니터링 UI
┃  ┣ 📜 battery.ui              # 이차전지 모듈 현황 모니터링 UI
┃  ┣ 📜 setting.ui              # 설정 UI
┃  ┗ 📜 information.ui          # 정보 UI
┗ 📂 PyQt_Service          # 기능 로직 관리  
   ┣ 📂 Dashboard               # 대시보드 페이지 관련 로직  
   ┃  ┣ 📜 __init__.py                  # 패키지 초기화
   ┃  ┣ 📜 battery_status_manager.py    # 3개 배터리 모듈의 충전 상태 표시 및 갱신
   ┃  ┣ 📜 clock_manager.py             # 현재 시각을 hh:mm:ss 형식으로 실시간 표시
   ┃  ┣ 📜 connection_status_manager.py # 시스템 연결 상태 모니터링 및 표시
   ┃  ┣ 📜 dashboard_controller.py      # 대시보드 전체 기능 통합 제어
   ┃  ┣ 📜 dashboard_graph_manager.py   # 전압,전류,전력량 그래프 관리 및 시각화
   ┃  ┣ 📜 load_power_manager.py        # 태양광 데이터 기반 실시간 부하 전력 표시
   ┃  ┗ 📜 warning_manager.py           # 이상 상태 감지 및 경고 메시지 표시
   ┣ 📂 Monitoring              # 모니터링 페이지 관련 로직  
   ┃  ┣ 📂 sample                       # csv 샘플 데이터
   ┃  ┣ 📜 __init__.py                  # 패키지 초기화
   ┃  ┣ 📜 csv_exporter.py              # CSV 파일 표 형태로 로드
   ┃  ┣ 📜 data_loader.py               # CSV 데이터 로드 밑 전처리
   ┃  ┣ 📜 data_resampler.py            # 시간 주기별 데이터 리샘플링 (1분, 10분, 1시간, 24시간)
   ┃  ┣ 📜 graph_manager.py             # Matplotlib 기반 그래프 표시 및 갱신 
   ┃  ┣ 📜 monitoring_controller.py     # 모듈 통합 제어
   ┃  ┗ 📜 view_manager.py              # 드롭박스/버튼 이벤트 관리 및 그래프 업데이트 로직
   ┗ 📂 Setting                 # 설정 페이지 관련 로직  
      ┣ 📜 __init__.py                  # 패키지 초기화  
      ┣ 📜 setting_controller.py        # 설정 페이지의 중앙 컨트롤러  
      ┣ 📜 usb_port_manager.py          # USB 포트 탐색 및 적용  
      ┣ 📜 charge_limit_manager.py      # 배터리 충전 한계 설정   
      ┣ 📜 sensor_reset_manager.py      # 센서 리셋  
      ┣ 📜 voltage_threshold_manager.py # 임계 전압 설정  
      ┣ 📜 reconnect_manager.py         # 통신 재연결  
      ┗ 📜 config_apply_manager.py      # 설정 저장 및 기본값 복원  
```


## 구현할 기능 및 현재 진행 상황

### 1️⃣ 대시보드
1. ✅ 배터리 모듈 3개의 충전량을 각각 표시
2. ✅ 현재 시각을 hh:mm:ss로 실시간 표시
3. ❌ 부하 전력 표시
4. ❌ 연결 상태를 정상/끊어짐 표시
5. ✅ 전압, 전류, 전력량을 하나의 미니 그래프로 표시
6. ❌ 경고 메시지 표시/ 없으면 정상

### 2️⃣ 태양광 발전 현황 모니터링
1. ✅ 그래프의 데이터 주기 단위를 설정하기 위한 Pandas를 이용한 데이터 그룹화 (1m, 10m, 1h, 1d)
2. ✅ 1분 주기 데이터는 가장 최근 데이터의 측정 시간을 기준으로 (2시간, 3시간, 4시간, 6시간) 전 까지의 데이터를 matplotlib을 이용해 그래프로 그려냄
3. ✅ 10분 주기 데이터는 가장 최근 데이터의 측정 시간을 기준으로 (6시간, 12시간) 전 까지의 데이터를 matplotlib을 이용해 그래프로 나타냄
4. ✅ 한시간은 주기 데이터는 가장 최근 데이터의 측정 시간을 기준으로 24시간(하루) 전 까지의 데이터를 matplotlib을 이용해 그래프로 나타냄
5. ✅ 하루단위 주기 데이터는 가장 최근 데이터의 측정 시간을 기준으로 7일전(일주일) 전 까지의 데이터를 matplotlib을 이용해 그래프로 나타냄
6. ✅ 위 데이터 들은 그룹시 평균 데이터로 나타내며, GUI에서 드롭박스를 통해 주기를 변경 할 수 있음
7. ✅ 전압(V), 전류(A), 전력량(W), 누적 전력량을 각각의 칸에 그려낸 그래프를 연동
8. ✅ 실제 수집된 데이터를 표(csv)로 보여주는 버튼

### 3️⃣ 이차전지 모듈 상태 모니터링
1. ✅ 위 태양광 발전 현황 모니터링과 동일하며, 보여주는 데이터는 1S, 2S, 3S, Total 배터리 전압 

### 4️⃣ 설정
1. ✅ USB 포트를 변경하는 드롭 박스
2. ✅ 배터리 충전 한계를 설정하는 입력칸 & 버튼
3. ✅ 센서 리셋 버튼
4. ✅ 임계 전압을 조절하는 입력칸  & 버튼
5. ✅ 통신 재연결 버튼
6. ✅ 변경사항 적용 & 기본값 복원 버튼 추가
