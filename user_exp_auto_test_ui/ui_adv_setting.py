from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QCheckBox,QLineEdit,QSlider,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,QRadioButton
)
from test_process import Basic_Config
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from functools import partial
import sys

class AdvanceSetting(QWidget):
    b_config:Basic_Config = None
    # Signal will send any Python object, including class instances
    setting_changed = pyqtSignal(object)
    def __init__(self, b_config:Basic_Config):
        super().__init__()
        self.b_config = b_config
        self.setWindowTitle("Advance Setting")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.ui_renew()
 
    def init_ui(self):

        self.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: navy;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                margin-top: 10px;
                background-color: #F0F8FF;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px;
            }
        """)

        def make_title(text):
            label = QLabel(text)
            label.setStyleSheet("font-size: 16px; font-weight: bold;")
            return label



        layout = QVBoxLayout()

        # --- system setting ---
        system_group = QGroupBox("System Setting")
        system_setting_laylout = QVBoxLayout()

        # timeout_s
        tos_layout = QHBoxLayout()
        self.label_tos = QLabel('Select Timeout (seconds):')
        self.value_tos = QLabel('30')  # Default value
        self.value_tos.setAlignment(Qt.AlignCenter)
        self.value_tos.setStyleSheet('font-size: 16px;')
        self.slider_timeout = QSlider(Qt.Horizontal)
        self.slider_timeout.setMinimum(1)
        self.slider_timeout.setMaximum(60)
        self.slider_timeout.setValue(30)
        self.slider_timeout.setTickInterval(1)
        self.slider_timeout.setTickPosition(QSlider.TicksBelow)
        self.slider_timeout.valueChanged.connect(partial(self.update_slider_value,"timeout_s"))
        tos_layout.addWidget(self.label_tos)
        tos_layout.addWidget(self.slider_timeout)
        tos_layout.addWidget(self.value_tos)

        #continue_fail_limit
        cfl_layout = QHBoxLayout()
        self.label_cfl = QLabel('Maximum Consecutive Failure times:')
        self.value_cfl = QLabel('5')  # Default value
        self.value_cfl.setAlignment(Qt.AlignCenter)
        self.value_cfl.setStyleSheet('font-size: 16px;')
        self.slider_cfl = QSlider(Qt.Horizontal)
        self.slider_cfl.setMinimum(1)
        self.slider_cfl.setMaximum(10)
        self.slider_cfl.setValue(5)
        self.slider_cfl.setTickInterval(1)
        self.slider_cfl.setTickPosition(QSlider.TicksBelow)
        self.slider_cfl.valueChanged.connect(partial(self.update_slider_value,"continue_fail_limit"))
        cfl_layout.addWidget(self.label_cfl)
        cfl_layout.addWidget(self.slider_cfl)
        cfl_layout.addWidget(self.value_cfl)

        #test_retry_times
        trt_layout = QHBoxLayout()
        self.label_trt = QLabel('Retry Times:')
        self.value_trt = QLabel('3')  # Default value
        self.value_trt.setAlignment(Qt.AlignCenter)
        self.value_trt.setStyleSheet('font-size: 16px;')
        self.slider_trt = QSlider(Qt.Horizontal)
        self.slider_trt.setMinimum(1)
        self.slider_trt.setMaximum(10)
        self.slider_trt.setValue(3)
        self.slider_trt.setTickInterval(1)
        self.slider_trt.setTickPosition(QSlider.TicksBelow)
        self.slider_trt.valueChanged.connect(partial(self.update_slider_value,"test_retry_times"))
        trt_layout.addWidget(self.label_trt)
        trt_layout.addWidget(self.slider_trt)
        trt_layout.addWidget(self.value_trt)

        system_setting_laylout.addLayout(tos_layout)
        system_setting_laylout.addLayout(cfl_layout)
        #system_setting_laylout.addLayout(trt_layout)
        system_group.setLayout(system_setting_laylout)

        # --- power state setting ---
        power_state_group = QGroupBox("Power State Setting")
        power_state_laylout = QVBoxLayout()
        #sleep_time_s
        sts_layout = QHBoxLayout()
        self.label_sts = QLabel('Sleep Time (s):')
        self.value_sts = QLabel('180')  # Default value
        self.value_sts.setAlignment(Qt.AlignCenter)
        self.value_sts.setStyleSheet('font-size: 16px;')
        self.slider_sts = QSlider(Qt.Horizontal)
        self.slider_sts.setMinimum(1)
        self.slider_sts.setMaximum(3600)
        self.slider_sts.setValue(180)
        self.slider_sts.setTickInterval(1)
        self.slider_sts.setTickPosition(QSlider.TicksBelow)
        self.slider_sts.valueChanged.connect(partial(self.update_slider_value,"sleep_time_s"))
        sts_layout.addWidget(self.label_sts)
        sts_layout.addWidget(self.slider_sts)
        sts_layout.addWidget(self.value_sts)

        #wake_up_time_s
        wuts_layout = QHBoxLayout()
        self.label_wuts = QLabel('Idle Time (s):')
        self.value_wuts = QLabel('60')  # Default value
        self.value_wuts.setAlignment(Qt.AlignCenter)
        self.value_wuts.setStyleSheet('font-size: 16px;')
        self.slider_wuts = QSlider(Qt.Horizontal)
        self.slider_wuts.setMinimum(1)
        self.slider_wuts.setMaximum(3600)
        self.slider_wuts.setValue(60)
        self.slider_wuts.setTickInterval(1)
        self.slider_wuts.setTickPosition(QSlider.TicksBelow)
        self.slider_wuts.valueChanged.connect(partial(self.update_slider_value,"wake_up_time_s"))
        wuts_layout.addWidget(self.label_wuts)
        wuts_layout.addWidget(self.slider_wuts)
        wuts_layout.addWidget(self.value_wuts)

        power_state_laylout.addLayout(sts_layout)
        power_state_laylout.addLayout(wuts_layout)
        power_state_group.setLayout(power_state_laylout)

        # ---functional setting ---
        functional_group = QGroupBox("Functional Setting")
        functional_laylout = QFormLayout()

        #teams_url
        self.led_team_url = QLineEdit()
        functional_laylout.addRow("Teams meeting URL:",self.led_team_url)
        #output_source : 2
        self.combo_output_source = QComboBox()
        self.combo_output_source.addItems(["Teams_bot", "Local_audio","Local_video","Teams_Local_audio","Youtube"])
        functional_laylout.addRow("Environment Source:",self.combo_output_source)

        #output_source_play_time_s
        ospts_layout = QHBoxLayout()
        self.label_ospts = QLabel('output source play time (s):')
        self.value_ospts = QLabel('20')  # Default value
        self.value_ospts.setAlignment(Qt.AlignCenter)
        self.value_ospts.setStyleSheet('font-size: 16px;')
        self.slider_ospts = QSlider(Qt.Horizontal)
        self.slider_ospts.setMinimum(1)
        self.slider_ospts.setMaximum(3600)
        self.slider_ospts.setValue(20)
        self.slider_ospts.setTickInterval(1)
        self.slider_ospts.setTickPosition(QSlider.TicksBelow)
        self.slider_ospts.valueChanged.connect(partial(self.update_slider_value,"output_source_play_time_s"))
        ospts_layout.addWidget(self.label_ospts)
        ospts_layout.addWidget(self.slider_ospts)
        ospts_layout.addWidget(self.value_ospts)

        functional_laylout.addRow(ospts_layout)

        #headset_setting : 0
        self.combo_headset_setting = QComboBox()
        self.combo_headset_setting.addItems(["idle", "turn_on_off"])
        functional_laylout.addRow("Headset Setting :",self.combo_headset_setting)
        
     
        functional_group.setLayout(functional_laylout) 
        self.btn_confirm = QPushButton("Save")
        self.btn_confirm.clicked.connect(self.send_setting)
        
        layout.addWidget(system_group)
        layout.addWidget(power_state_group)
        layout.addWidget(functional_group)
        layout.addWidget(self.btn_confirm)
        self.setLayout(layout)

    def ui_renew(self):
        # showing the UI status according to the last time status
        # --- system setting ---
        self.slider_timeout.setValue(self.b_config.timeout_s)
        self.slider_cfl.setValue(self.b_config.continue_fail_limit)
        self.slider_trt.setValue(self.b_config.test_retry_times)
        # --- Power states Selection ---
        self.slider_sts.setValue(self.b_config.sleep_time_s)
        self.slider_wuts.setValue(self.b_config.wake_up_time_s)
        # ---functional setting ---
        self.led_team_url.setText(self.b_config.teams_url)
        self.combo_output_source.setCurrentIndex(self.b_config.ENV_source)
        self.combo_headset_setting.setCurrentIndex(self.b_config.headset_setting)
     
        


    def update_slider_value(self,value_name,value):
        match value_name:
            case "timeout_s":
                 self.value_tos.setText(str(value))
            case "continue_fail_limit":
                 self.value_cfl.setText(str(value))
            case "test_retry_times":
                 self.value_trt.setText(str(value))
            case "sleep_time_s":
                 self.value_sts.setText(str(value))
            case "wake_up_time_s":
                 self.value_wuts.setText(str(value))
            case "output_source_play_time_s":
                 self.value_ospts.setText(str(value))
    

    def send_setting(self):
        data = self.b_config
        # showing the UI status according to the last time status
        # --- system setting ---
        data.timeout_s = self.slider_timeout.value()
        data.continue_fail_limit = self.slider_cfl.value()
        data.test_retry_times = self.slider_trt.value()
        # --- Power states Selection ---
        data.sleep_time_s = self.slider_sts.value()
        data.wake_up_time_s = self.slider_wuts.value()
        # ---functional setting ---
        data.teams_url = self.led_team_url.text()
        data.ENV_source = self.combo_output_source.currentIndex()
        data.headset_setting = self.combo_headset_setting.currentIndex()
        data.output_source_play_time_s = self.slider_ospts.value() 
        
        self.setting_changed.emit(data)
        self.close()

 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvanceSetting()
    window.show()
    sys.exit(app.exec_())



        
    
       