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
        self.ax.tick_params(axis='x', labelsize=11)
        self.ax.tick_params(axis='y', labelsize=11)

TITLE_FONTSIZE = 16
LABEL_FONTSIZE = 14

class SolarAndBatteryStatusMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("태양광 모니터링 시스템")
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
            "1일(전체)": ('1day', 0, 1)
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

        df_merged = pd.merge(
            df_battery[['Date', 'Time', 'Total Voltage']],
            df_solar[['Date', 'Time', '전류(A)', '누적 전력량(Wh)']],
            on=['Date', 'Time'],
            how='inner'
        )

        df_merged['Datetime'] = pd.to_datetime(df_merged['Date'] + ' ' + df_merged['Time'])
        df_merged.set_index('Datetime', inplace=True)
        df_merged['누적 전력량(kWh)'] = df_merged['누적 전력량(Wh)'] / 1000
        df_merged['누적 최대 전류(A)'] = df_merged['전류(A)'].cummax()

        self.df_plot = df_merged[['Total Voltage', '전류(A)', '누적 최대 전류(A)', '누적 전력량(kWh)']].copy()

        self.np_datetime_str = df_merged.index.strftime('%Y-%m-%d %H:%M:%S').to_numpy()
        self.np_x = np.arange(len(self.df_plot))
        self.time_labels = df_merged.index.strftime('%H:%M:%S').to_numpy()

        self.np_v_total = self.df_plot['Total Voltage'].to_numpy()
        self.np_i_current = self.df_plot['전류(A)'].to_numpy()
        self.np_i_max = self.df_plot['누적 최대 전류(A)'].to_numpy()
        self.np_e_cum = self.df_plot['누적 전력량(kWh)'].to_numpy()

        self.v_min, self.v_max = self.np_v_total.min(), self.np_v_total.max()
        self.c_min, self.c_max = self.np_i_current.min(), self.np_i_current.max()
        self.mc_min, self.mc_max = self.np_i_max.min(), self.np_i_max.max()
        self.e_min, self.e_max = self.np_e_cum.min(), self.np_e_cum.max()

    def setup_ui(self):
        ylabel_opts = {'labelpad': 10}

        self.canvas_v_total = MplCanvas(self)
        self.layout.addWidget(self.canvas_v_total, 0, 0)
        self.canvas_v_total.ax.set_title('전압(V)', fontsize=TITLE_FONTSIZE)
        self.canvas_v_total.ax.set_ylabel('Voltage (V)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_v_total, = self.canvas_v_total.ax.plot([], [], 'darkorange', label='전압')

        self.canvas_current = MplCanvas(self)
        self.layout.addWidget(self.canvas_current, 0, 1)
        self.canvas_current.ax.set_title('전류(A)', fontsize=TITLE_FONTSIZE)
        self.canvas_current.ax.set_ylabel('Current (A)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_current, = self.canvas_current.ax.plot([], [], 'darkcyan', label='전류')

        self.canvas_max_current = MplCanvas(self)
        self.layout.addWidget(self.canvas_max_current, 1, 0)
        self.canvas_max_current.ax.set_title('최대 전류(A)', fontsize=TITLE_FONTSIZE)
        self.canvas_max_current.ax.set_ylabel('Max Current (A)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_max_current, = self.canvas_max_current.ax.plot([], [], 'red', linewidth=2, label='최대 전류')

        self.canvas_energy_cum = MplCanvas(self)
        self.layout.addWidget(self.canvas_energy_cum, 1, 1)
        self.canvas_energy_cum.ax.set_title('누적 전력(kWh)', fontsize=TITLE_FONTSIZE)
        self.canvas_energy_cum.ax.set_ylabel('Power (kWh)', fontsize=LABEL_FONTSIZE, **ylabel_opts)
        self.line_energy_cum, = self.canvas_energy_cum.ax.plot([], [], 'purple', linewidth=2, label='누적 전력')

        for canvas in [self.canvas_v_total, self.canvas_current, self.canvas_max_current, self.canvas_energy_cum]:
            canvas.ax.set_xlabel('시간 (Time)', fontsize=LABEL_FONTSIZE, labelpad=15)

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
        mode_key = next((v[0] for k, v in self.simulation_modes.items() if k == mode_name), None)
        if mode_key:
            self.set_simulation_mode(mode_key)

    def set_y_limits(self):
        v_range = self.v_max - self.v_min
        self.canvas_v_total.ax.set_ylim(self.v_min - v_range * 0.1, self.v_max + v_range * 0.1)

        c_range = self.c_max - self.c_min
        c_y_min = self.c_min - c_range * 0.2 if self.c_min < 0 else -1
        c_y_max = self.c_max + c_range * 0.2 if self.c_max > 0 else 1
        self.canvas_current.ax.set_ylim(c_y_min, c_y_max)

        mc_range = self.mc_max - self.mc_min
        mc_y_min = self.mc_min - mc_range * 0.2 if self.mc_min < 0 else -1
        mc_y_max = self.mc_max + mc_range * 0.2 if self.mc_max > 0 else 1
        self.canvas_max_current.ax.set_ylim(mc_y_min, mc_y_max)

        e_range = self.e_max - self.e_min
        self.canvas_energy_cum.ax.set_ylim(self.e_min - e_range * 0.1, self.e_max + e_range * 0.1)

    def set_simulation_mode(self, mode):
        self.timer.stop()
        self.data_index = 0

        self.line_v_total.set_data([], [])
        self.line_current.set_data([], [])
        self.line_max_current.set_data([], [])
        self.line_energy_cum.set_data([], [])

        for canvas in [self.canvas_v_total, self.canvas_current, self.canvas_max_current, self.canvas_energy_cum]:
            canvas.draw()

        mode_info_item = next(((k, v) for k, v in self.simulation_modes.items() if v[0] == mode), None)
        if not mode_info_item: return

        mode_name, (_, interval, step) = mode_info_item
        self.current_data_step = step

        if mode == '1day':
            time_interval = pd.Timedelta(hours=3)
            time_diff_sec = (pd.to_datetime(self.np_datetime_str[1]) - pd.to_datetime(self.np_datetime_str[0])).total_seconds()
            
            index_step = int(time_interval.total_seconds() / time_diff_sec) if time_diff_sec > 0 else 180

            new_ticks_indices = np.arange(0, self.max_data_index + 1, index_step)
            new_ticks_labels = [self.time_labels[i] for i in new_ticks_indices if i < len(self.time_labels)]
        else:
            new_ticks_indices = np.arange(0, self.max_data_index + 1, step)
            new_ticks_labels = [self.time_labels[i] for i in new_ticks_indices if i < len(self.time_labels)]


        for canvas in [self.canvas_v_total, self.canvas_current, self.canvas_max_current, self.canvas_energy_cum]:
            canvas.ax.set_xticks(new_ticks_indices)
            canvas.ax.set_xticklabels(new_ticks_labels, rotation=45, ha='right')

        if mode == '1day':
            self.data_index = self.max_data_index
            self.status_label.setText(f"모드: **{mode_name}** (전체 데이터 표시)")
            self.status_label.setStyleSheet("color: darkgreen;")
        else:
            self.status_label.setText(f"모드: **{mode_name}** (샘플링/간격: {step} | {interval}ms)")
            self.status_label.setStyleSheet("color: blue;")
            self.timer.setInterval(interval)
            self.timer.start()

        self.update_plot()

    def update_plot(self):
        if self.data_index <= self.max_data_index:
            current_idx = self.data_index + 1
            x_data = self.np_x[:current_idx:self.current_data_step]

            self.line_v_total.set_data(x_data, self.np_v_total[:current_idx:self.current_data_step])
            self.line_current.set_data(x_data, self.np_i_current[:current_idx:self.current_data_step])
            self.line_max_current.set_data(x_data, self.np_i_max[:current_idx:self.current_data_step])
            self.line_energy_cum.set_data(x_data, self.np_e_cum[:current_idx:self.current_data_step])

            display_window = 500
            for canvas in [self.canvas_v_total, self.canvas_current, self.canvas_max_current, self.canvas_energy_cum]:
                if self.data_index == self.max_data_index:
                    canvas.ax.set_xlim(0, self.max_data_index + 1)
                elif current_idx > display_window:
                    canvas.ax.set_xlim(current_idx - display_window, current_idx + self.current_data_step)
                else:
                    canvas.ax.set_xlim(0, current_idx + self.current_data_step)
                canvas.draw()

            current_datetime_str = self.np_datetime_str[self.data_index] if self.data_index < len(self.np_datetime_str) else "N/A"
            self.status_label.setText(
                f"시간: {current_datetime_str} | 인덱스: {self.data_index + 1}/{self.max_data_index + 1}"
            )

            if self.data_index < self.max_data_index:
                self.data_index += self.current_data_step
            elif self.data_index == self.max_data_index and self.timer.isActive():
                self.timer.stop()
                self.status_label.setText(f"✅ 시뮬레이션 완료! (최종 시간: **{current_datetime_str}**)")

if __name__ == '__main__':
    if not os.path.exists('data sample_battery.csv') or not os.path.exists('data sample_solar3.csv'):
        print("오류: 필요한 파일이 없습니다.")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = SolarAndBatteryStatusMonitorApp()
    window.show()
    sys.exit(app.exec_())