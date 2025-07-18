from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QCheckBox,QLineEdit,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,QRadioButton
)
from PyQt5.QtCore import Qt
import sys
import test_process
from test_process import Basic_Config
from test_process import Power_States
from utils import log  as logger
from bt_control import BluetoothControl
from ui_adv_setting import AdvanceSetting
from functools import partial

class BTTestApp(QWidget):
    b_config:Basic_Config = None
    def __init__(self, b_config:Basic_Config):
        super().__init__()
        self.b_config = b_config
        self.setWindowTitle("User Experience Auto Test")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.bt_device_check()
        self.ui_renew()
        

    def init_ui(self):
        layout = QVBoxLayout()

        # --- setting ---
        setting_layout = QHBoxLayout()
        self.btn_ardu_check = QPushButton("Arduino Check")
        self.btn_bt_check = QPushButton("BT Device Check")
        self.btn_advance_setting = QPushButton("Advance Setting")
        self.btn_ardu_check.clicked.connect(self.serial_port_check)
        self.btn_bt_check.clicked.connect(self.bt_device_check)
        self.btn_advance_setting.clicked.connect(self.advance_setting)
        setting_layout.addWidget(self.btn_ardu_check)
        setting_layout.addWidget(self.btn_bt_check)
        setting_layout.addWidget(self.btn_advance_setting)


        # --- Device Selection ---
        device_group = QGroupBox("Device Selection")
        device_layout = QFormLayout()

        self.led_headset = QLineEdit()
        self.led_headset.setReadOnly(True)

        self.led_mouse = QLineEdit()
        self.led_mouse.setReadOnly(True)

        device_layout.addRow("Headset:", self.led_headset)
        device_layout.addRow("Mouse:", self.led_mouse)
        device_group.setLayout(device_layout)

        # --- Power states Selection ---
        power_states_group = QGroupBox("DUT Power States")
        power_states_layout = QHBoxLayout()

        self.rbtn_idle = QRadioButton("IDLE")
        self.rbtn_ms = QRadioButton("MS")
        self.rbtn_s4 = QRadioButton("S4")

        self.rbtn_idle.clicked.connect(partial(self.power_states_setting,Power_States.idle.value))
        self.rbtn_ms.clicked.connect(partial(self.power_states_setting,Power_States.go_to_s3.value))
        self.rbtn_s4.clicked.connect(partial(self.power_states_setting,Power_States.go_to_s4.value))

        power_states_layout.addWidget(self.rbtn_idle)
        power_states_layout.addWidget(self.rbtn_ms)
        power_states_layout.addWidget(self.rbtn_s4)
        power_states_group.setLayout(power_states_layout)

        # --- Test Case Selection ---
        test_case_group = QGroupBox("Test Case Selection")
        test_layout = QVBoxLayout()

        self.ck_btn_mouse = QCheckBox("Mouse Function Test")
        self.ck_btn_h_input = QCheckBox("Headset Input Test")
        self.ck_btn_h_output = QCheckBox("Headset Output Test")

        self.ck_btn_mouse.stateChanged.connect(partial(self.test_case_setting,'do_mouse_flag'))
        self.ck_btn_h_input.stateChanged.connect(partial(self.test_case_setting,'do_headset_input_flag'))
        self.ck_btn_h_output.stateChanged.connect(partial(self.test_case_setting,'do_headset_output_flag'))
        
        test_layout.addWidget(self.ck_btn_mouse)
        test_layout.addWidget(self.ck_btn_h_input)
        test_layout.addWidget(self.ck_btn_h_output)
        test_case_group.setLayout(test_layout)

        # --- Log Output ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.run_test)
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.quit_button)

        # --- Combine All Layouts ---
        layout.addLayout(setting_layout)
        layout.addWidget(device_group)
        layout.addWidget(power_states_group)
        layout.addWidget(test_case_group)
        layout.addWidget(QLabel("Test Progress:"))
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def power_states_setting(self, power_states:int):
        #setting the power states
        setattr(self.b_config,"power_state",power_states)

    def test_case_setting(self, flag_name:str, state):
        #setting the test case
        is_checked = state == Qt.CheckState.Checked
        setattr(self.b_config,flag_name,is_checked)

    def log_to_ui(self,msg):
        # Run test logic and log output to UI and log file
        self.log_output.append(msg)
        logger.info(msg)

    def serial_port_check(self):
        #check arduino board existed 
        self.log_output.clear()  # Clear previous logs
        test_process.get_arduino_port(port=self.b_config.target_port_desc, log_callback=self.log_to_ui)

    def run_test(self):
        #run the main test process
        test_process.run_test(b_config=self.b_config,log_callback= self.log_to_ui)

    def bt_device_check(self):
        #checking the bt device existed, like headset, mouse
        headset = BluetoothControl.find_headset()
        self.led_headset.setText(headset)

    def advance_setting(self):
        self.settings_window = AdvanceSetting(self.b_config)
        self.settings_window.setting_changed.connect(self.apply_setting)
        self.settings_window.show()

    def apply_setting(self, basic_config:Basic_Config):
        self.b_config = basic_config
        self.log_output.append(str(self.b_config))
    
    def ui_renew(self):
        # showing the UI status according to the last time status
        # --- Power states Selection ---
        match self.b_config.power_state:
            case Power_States.idle.value:
                self.rbtn_idle.setChecked(True)
            case Power_States.go_to_s3.value:
                self.rbtn_ms.setChecked(True)
            case Power_States.go_to_s4.value:
                self.rbtn_s4.setChecked(True)
        # --- Test Case Selection ---
        if b_config.do_headset_input_flag:
            self.ck_btn_mouse.setChecked(True)
        if b_config.do_headset_output_flag:
            self.ck_btn_h_output.setChecked(True)
        if b_config.do_headset_input_flag:
            self.ck_btn_h_input.setChecked(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    b_config = test_process.load_basic_config("config_basic.yaml")
    window = BTTestApp(b_config=b_config)
    window.show()
    sys.exit(app.exec_())
