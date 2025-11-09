import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QHBoxLayout, QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    try:
        plt.rcParams['font.family'] = 'NanumGothic'
    except:
        pass

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=5, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.margins(x=0.01)

        self.fig.subplots_adjust(bottom=0.22, top=0.9, left=0.15, right=0.95)

        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, prune='both'))
        self.ax.xaxis.set_major_formatter(ticker.NullFormatter()) 

        self.ax.tick_params(axis='x', labelsize=11)
        self.ax.tick_params(axis='y', labelsize=11)

TITLE_FONTSIZE = 16
LABEL_FONTSIZE = 14

class CombinedBatteryMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("배터리 모니터링 시스템")
        self.setGeometry(100, 100, 1600, 1000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.data_load_and_preprocess()

        self.data_index = 0
        self.max_data_index = len(self.np_x) - 1

        self.simulation_modes = {
            "1분": ('1min', 500, 1),
            "10분": ('10min', 200, 10),
            "30분": ('30min', 100, 30),
            "1시간": ('1hr', 50, 60),
            "1일 (전체)": ('1day', 0, 1) 
        }
        
        self.current_data_step = 1 

        self.setup_ui()
        self.set_y_limits()

        self.set_simulation_mode('1min') 
        self.mode_selector.setCurrentText('1분 (매우 느림)')

    def data_load_and_preprocess(self):
        file_battery = 'data sample_battery.csv'
        file_solar = 'data sample_solar3.csv'

        def safe_read_csv(file_name):
            try:
                return pd.read_csv(file_name, encoding='cp949')
            except UnicodeDecodeError:
                return pd.read_csv(file_name, encoding='utf-8')
            except FileNotFoundError:
                print(f"오류: 파일 '{file_name}'을 찾을 수 없습니다.")
                sys.exit(1)
            except Exception as e:
                print(f"오류: 데이터 로드 중 문제 발생. {e}")
                sys.exit(1)

        df_battery = safe_read_csv(file_battery)
        df_solar = safe_read_csv(file_solar)

        df_merged = pd.merge(df_battery, df_solar[['Date', 'Time', '전류(A)']],
                             on=['Date', 'Time'],
                             how='inner')

        df_merged['Datetime'] = pd.to_datetime(df_merged['Date'] + ' ' + df_merged['Time'])
        df_merged.set_index('Datetime', inplace=True)

        self.df_plot = df_merged[['1S Voltage', 'Total Voltage', '전류(A)']].copy()

        self.np_datetime_str = df_merged.index.strftime('%Y-%m-%d %H:%M:%S').to_numpy()
        self.np_x = np.arange(len(self.df_plot))

        self.time_labels = df_merged.index.strftime('%H:%M:%S').to_numpy()

        self.time_ticks_indices = np.arange(0, len(self.np_x), 60 * 3) 
        self.time_ticks_labels = [self.time_labels[i] for i in self.time_ticks_indices if i < len(self.time_labels)]


        self.np_v1s = self.df_plot['1S Voltage'].to_numpy()
        self.np_i2s = self.df_plot['전류(A)'].to_numpy()

        np_vtotal = self.df_plot['Total Voltage'].to_numpy()
        v_norm = (np_vtotal - np_vtotal.min()) / (np_vtotal.max() - np_vtotal.min())
        self.np_t3s = v_norm * (45 - 20) + 20 + np.random.normal(0, 0.5, len(np_vtotal))

        self.np_v_soc = v_norm * 100

        self.v1s_min, self.v1s_max = self.np_v1s.min(), self.np_v1s.max()
        self.i2s_min, self.i2s_max = self.np_i2s.min(), self.np_i2s.max()
        self.t3s_min, self.t3s_max = self.np_t3s.min(), self.np_t3s.max()
        self.soc_min, self.soc_max = self.np_v_soc.min(), self.np_v_soc.max()


    def setup_ui(self):

        ylabel_opts = {'labelpad': 10}

        self.canvas_v1s = MplCanvas(self)
        self.layout.addWidget(self.canvas_v1s, 0, 0)
        self.canvas_v1s.ax.set_title('1S 모듈 전압(V)', fontsize=TITLE_FONTSIZE)
        self.canvas_v1s.ax.set_ylabel('Voltage (V)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_v1s, = self.canvas_v1s.ax.plot([], [], 'darkorange', label='1S 전압')

        self.canvas_i2s = MplCanvas(self)
        self.layout.addWidget(self.canvas_i2s, 0, 1)
        self.canvas_i2s.ax.set_title('2S 모듈 전류(A)', fontsize=TITLE_FONTSIZE)
        self.canvas_i2s.ax.set_ylabel('Current (A)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_i2s, = self.canvas_i2s.ax.plot([], [], 'darkcyan', label='2S 전류')

        self.canvas_t3s = MplCanvas(self)
        self.layout.addWidget(self.canvas_t3s, 1, 0)
        self.canvas_t3s.ax.set_title('3S 모듈 온도(°C)', fontsize=TITLE_FONTSIZE)
        self.canvas_t3s.ax.set_ylabel('Temperature (°C)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_t3s, = self.canvas_t3s.ax.plot([], [], 'red', linewidth=2, label='3S 온도')

        self.canvas_soc_total = MplCanvas(self)
        self.layout.addWidget(self.canvas_soc_total, 1, 1)
        self.canvas_soc_total.ax.set_title('전체 팩 SOC(%)', fontsize=TITLE_FONTSIZE)
        self.canvas_soc_total.ax.set_ylabel('SOC (%)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_soc_total, = self.canvas_soc_total.ax.plot([], [], 'purple', linewidth=2, label='전체 SOC')

        for canvas in [self.canvas_v1s, self.canvas_i2s, self.canvas_t3s, self.canvas_soc_total]:
            canvas.ax.set_xlabel('시간 (Time)', fontsize=LABEL_FONTSIZE, labelpad=15)
            canvas.ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d')) 


        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)

        self.mode_selector = QComboBox()
        self.mode_selector.setFont(QFont('Malgun Gothic', 11))
        self.mode_selector.setStyleSheet("padding: 5px;")

        for name in self.simulation_modes.keys():
            self.mode_selector.addItem(name)

        self.mode_selector.currentIndexChanged.connect(self._handle_mode_change)

        mode_label = QLabel("시뮬레이션 모드:")
        mode_label.setFont(QFont('Malgun Gothic', 11))
        control_layout.addWidget(mode_label)
        control_layout.addWidget(self.mode_selector)
        control_layout.addStretch(1)

        self.status_label = QLabel("상태: 초기화 중...")
        self.status_label.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.status_label.setStyleSheet("color: blue;")

        bottom_widget = QWidget()
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.addWidget(control_widget, 0, 0, 1, 1)
        bottom_layout.addWidget(self.status_label, 0, 1, 1, 1, alignment=Qt.AlignCenter)
        bottom_layout.setColumnStretch(0, 3)
        bottom_layout.setColumnStretch(1, 1)

        self.layout.setRowStretch(2, 1)

        self.layout.addWidget(bottom_widget, 2, 0, 1, 2)

    def _handle_mode_change(self, index):
        mode_name = self.mode_selector.currentText()
        mode_info = next(((k, v) for k, v in self.simulation_modes.items() if k == mode_name), None)
        if mode_info:
            mode_key = mode_info[1][0]
            self.set_simulation_mode(mode_key)

    def set_y_limits(self):
        v1s_range = self.v1s_max - self.v1s_min
        self.canvas_v1s.ax.set_ylim(self.v1s_min - v1s_range * 0.1, self.v1s_max + v1s_range * 0.1)

        i2s_range = self.i2s_max - self.i2s_min
        i2s_y_min = self.i2s_min - i2s_range * 0.2 if self.i2s_min < 0 else -1
        i2s_y_max = self.i2s_max + i2s_range * 0.2 if self.i2s_max > 0 else 1
        self.canvas_i2s.ax.set_ylim(i2s_y_min, i2s_y_max)

        t3s_range = self.t3s_max - self.t3s_min
        self.canvas_t3s.ax.set_ylim(self.t3s_min - t3s_range * 0.1, self.t3s_max + t3s_range * 0.1)

        soc_y_min = -10
        soc_y_max = 105
        self.canvas_soc_total.ax.set_ylim(soc_y_min, soc_y_max)


    def set_simulation_mode(self, mode):

        self.timer.stop()
        self.data_index = 0

        self.line_v1s.set_data([], [])
        self.line_i2s.set_data([], [])
        self.line_t3s.set_data([], [])
        self.line_soc_total.set_data([], [])

        for canvas in [self.canvas_v1s, self.canvas_i2s, self.canvas_t3s, self.canvas_soc_total]:
            canvas.draw()

        mode_info_item = next(((k, v) for k, v in self.simulation_modes.items() if v[0] == mode), None)
        if not mode_info_item: return

        mode_name, (mode_key, interval, step) = mode_info_item
        self.current_data_step = step 
        
        # === X축 눈금 간격 동적 계산 및 설정 ===
        
        if mode == '1day':
            tick_step = 60 * 3  
        elif step == 60:
            tick_step = 60      
        elif step == 30:
            tick_step = 30      
        elif step == 10:
            tick_step = 10      
        elif step == 1:
            tick_step = 1       
        else:
            tick_step = 30
            
        new_ticks_indices = np.arange(0, self.max_data_index + 1, tick_step)
        new_ticks_labels = [self.time_labels[i] for i in new_ticks_indices if i < len(self.time_labels)]

        for canvas in [self.canvas_v1s, self.canvas_i2s, self.canvas_t3s, self.canvas_soc_total]:
            canvas.ax.set_xticks(new_ticks_indices)
            canvas.ax.set_xticklabels(new_ticks_labels, rotation=45, ha='right')
            
        # === 시뮬레이션 모드 로직 ===

        if mode == '1day':
            self.data_index = self.max_data_index
            self.status_label.setText(f"모드: **{mode_name}** (전체 데이터 표시)")
            self.status_label.setStyleSheet("color: darkgreen;")

        else:
            self.status_label.setText(f"모드: **{mode_name}** (샘플링/눈금 간격: {step}분, 시뮬레이션 간격: {interval}ms)")
            self.status_label.setStyleSheet("color: blue;")
            self.timer.setInterval(interval)
            self.timer.start()

        self.update_plot()


    def update_plot(self):

        if self.data_index <= self.max_data_index:

            current_x_data = self.np_x[:self.data_index + 1:self.current_data_step]
            current_v1s_data = self.np_v1s[:self.data_index + 1:self.current_data_step]
            current_i2s_data = self.np_i2s[:self.data_index + 1:self.current_data_step]
            current_t3s_data = self.np_t3s[:self.data_index + 1:self.current_data_step]
            current_soc_data = self.np_v_soc[:self.data_index + 1:self.current_data_step]
            
            self.line_v1s.set_data(current_x_data, current_v1s_data)
            self.line_i2s.set_data(current_x_data, current_i2s_data)
            self.line_t3s.set_data(current_x_data, current_t3s_data)
            self.line_soc_total.set_data(current_x_data, current_soc_data)

            current_idx = self.data_index + 1
            display_window = 500

            for canvas in [self.canvas_v1s, self.canvas_i2s, self.canvas_t3s, self.canvas_soc_total]:
                if self.data_index == self.max_data_index:
                    canvas.ax.set_xlim(0, self.max_data_index + 1)
                elif current_idx > display_window:
                    canvas.ax.set_xlim(current_idx - display_window, current_idx + self.current_data_step)
                else:
                    canvas.ax.set_xlim(0, current_idx + self.current_data_step)

                canvas.draw()


            current_datetime_str = self.np_datetime_str[self.data_index] if self.data_index < len(self.np_datetime_str) else "N/A"
            self.status_label.setText(
                f"시간: **{current_datetime_str}** | 인덱스: {self.data_index + 1}/{self.max_data_index + 1}"
            )

            next_index = self.data_index + self.current_data_step

            if next_index <= self.max_data_index:
                self.data_index = next_index
            else:
                self.data_index = self.max_data_index
                
            if self.data_index == self.max_data_index and self.timer.isActive():
                self.timer.stop()
                self.status_label.setText(f"✅ 시뮬레이션 완료! (최종 시간: **{current_datetime_str}**)")
                self.status_label.setStyleSheet("color: red;")


if __name__ == '__main__':
    if not os.path.exists('data sample_battery.csv') or not os.path.exists('data sample_solar3.csv'):
        print("오류: 필요한 파일 ('data sample_battery.csv' 또는 'data sample_solar3.csv')을 찾을 수 없습니다.")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = CombinedBatteryMonitorApp()
    window.show()
    sys.exit(app.exec_())