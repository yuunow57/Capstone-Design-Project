pip install PyQt5  
pip install numpy  
pip install pyqtgraph  
pip install pandas  
pip install matplotlib  
pip install pyserial  


📁 폴더 구조  

📦 Capstone_Design_Project  
┣ 📂 PyQt_GUI                 # GUI 실행 및 화면 관리 (stack.py 등)  
┗ 📂 PyQt_Service             # 기능 로직 관리  
&nbsp;┗ 📂 Setting               # 설정 페이지 관련 로직  
&nbsp;&nbsp;┣ 📜 __init__.py                  # 패키지 초기화  
&nbsp;&nbsp;┣ 📜 setting_controller.py        # 설정 페이지의 중앙 컨트롤러  
&nbsp;&nbsp;┣ 📜 usb_port_manager.py          # USB 포트 탐색 및 적용  
&nbsp;&nbsp;┣ 📜 charge_limit_manager.py      # 배터리 충전 한계 설정   
&nbsp;&nbsp;┣ 📜 sensor_reset_manager.py      # 센서 리셋  
&nbsp;&nbsp;┣ 📜 voltage_threshold_manager.py # 임계 전압 설정  
&nbsp;&nbsp;┣ 📜 reconnect_manager.py         # 통신 재연결  
&nbsp;&nbsp;┗ 📜 config_apply_manager.py      # 설정 저장 및 기본값 복원  
