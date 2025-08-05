from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QCheckBox,QLineEdit, QTableView,QSlider,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,QRadioButton
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem,QTextCursor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal ,QObject
import sys
import test_process
from test_process import Basic_Config
from test_process import Power_States
from utils import log  as logger
from bt_control import BluetoothControl
from ui_adv_setting import AdvanceSetting
from functools import partial
import threading
import copy
import yaml
from dataclasses import asdict
from multiprocessing import Process

done_event = threading.Event()

class LogSignal(QObject):
    log = pyqtSignal(str)
    cell = pyqtSignal(int,int,str)

class BTTestApp(QWidget):
    
    b_config:Basic_Config = None
    task_schedule:list[Basic_Config] = []
    test_thread:threading = None
    def __init__(self, b_config:Basic_Config):
        super().__init__()
        self.b_config = b_config
        self.setWindowTitle("User Experience Auto Test")
        self.setGeometry(100, 100, 800, 800)
        self.init_ui()
        self.bt_device_check()
        self.ui_renew()
        self.log_signal = LogSignal()
        self.log_signal.log.connect(self.log_to_ui)
        self.log_signal.cell.connect(self.update_cell)
       

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

        # --- Task schedule table ---
        task_schedule_group = QGroupBox("Test Case Selection")
        task_schedule_layout = QVBoxLayout()

        task_setting_laylout = QHBoxLayout()
        self.lab_test_times = QLabel('Test times:')
        self.value_tts = QLabel('1')  # Default value
        self.value_tts.setAlignment(Qt.AlignCenter)
        self.value_tts.setStyleSheet('font-size: 16px;')
        self.slider_test_times = QSlider(Qt.Horizontal)
        self.slider_test_times.setMinimum(1)
        self.slider_test_times.setMaximum(1000)
        self.slider_test_times.setValue(1)
        self.slider_test_times.setTickInterval(1)
        self.slider_test_times.setTickPosition(QSlider.TicksBelow)
        self.slider_test_times.valueChanged.connect(partial(self.update_slider_value,"test_times"))

        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(partial(self.task_schedule_setting,"add"))
        self.btn_delet = QPushButton("Delet")
        self.btn_delet.clicked.connect(partial(self.task_schedule_setting,"delet"))

        task_setting_laylout.addWidget(self.lab_test_times)
        task_setting_laylout.addWidget(self.slider_test_times)
        task_setting_laylout.addWidget(self.value_tts)
        task_setting_laylout.addWidget(self.btn_add)
        task_setting_laylout.addWidget(self.btn_delet)

        self.task_schedule_model = QStandardItemModel(0, 2) 
        self.task_schedule_model.setHorizontalHeaderLabels(["Power States", "Test Case", "times","Status"])
        table_view = QTableView()
        table_view.setModel(self.task_schedule_model)
        table_view.setColumnWidth(1, 400)
        task_schedule_layout.addLayout(task_setting_laylout)
        task_schedule_layout.addWidget(table_view)
        task_schedule_group.setLayout(task_schedule_layout)

        # --- Log Output ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.run_test)
        self.btn_quit = QPushButton("Quit")
        self.btn_quit.clicked.connect(self.close)
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_quit)

        # --- Combine All Layouts ---
        layout.addLayout(setting_layout)
        layout.addWidget(device_group)
        layout.addWidget(power_states_group)
        layout.addWidget(test_case_group)
        layout.addWidget(task_schedule_group)
        layout.addWidget(QLabel("Test Progress:"))
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def task_schedule_setting(self, name:str):
        match name:
            case "add":
                power_states = ""
                # power states:
                match self.b_config.power_state:
                    case Power_States.idle.value:
                        power_states+="Idle"
                    case Power_States.go_to_s3.value:
                        power_states+="MS"
                    case Power_States.go_to_s4.value:
                        power_states+="S4"
                # test case:
                test_case = ""
                if self.b_config.do_mouse_flag:
                    test_case += "mouse function "
                if self.b_config.do_headset_output_flag:
                    test_case += "headset_output "
                if self.b_config.do_headset_input_flag:
                    test_case += "headset_input "
                new_row = [QStandardItem(power_states),QStandardItem(test_case),QStandardItem(self.value_tts.text()), QStandardItem("idle")]
                self.task_schedule_model.appendRow(new_row)
                #deep copy the b_config
                new_task = copy.deepcopy(self.b_config)
                self.task_schedule.append(new_task)
            case "delet":
                row_count = self.task_schedule_model.rowCount()
                if row_count:
                    self.task_schedule_model.removeRow(row_count - 1)
                    self.task_schedule.pop()

    def power_states_setting(self, power_states:int):
        #setting the power states
        setattr(self.b_config,"power_state",power_states)

    def test_case_setting(self, flag_name:str, state):
        #setting the test case
        is_checked = state == Qt.CheckState.Checked
        setattr(self.b_config,flag_name,is_checked)

    def log_to_ui(self,msg:str):
        # Run test logic and log output to UI and log file
        #current_text = self.log_output.toPlainText()
        #updated_text = f"{msg}\n{current_text}"
        self.log_output.append(msg)
        self.log_output.moveCursor(QTextCursor.End)
        logger.info(msg)

    def serial_port_check(self):
        #check arduino board existed 
        self.log_output.clear()  # Clear previous logs
        test_process.get_arduino_port(port=self.b_config.target_port_desc, log_callback=self.log_to_ui)

    def run_test(self):
        #run the main test process
        def _run_test_process_in_background():
            row = 0
            for config in self.task_schedule:
                self.log_signal.cell.emit(row,3,"running...")
                done_event.clear()
                test_process.run_test(config,self.log_signal.log.emit,done_event)
                done_event.wait()
                self.log_signal.cell.emit(row,3,"Done")
                row+=1


        if self.btn_start.text() == "Start":    
            self.test_thread = threading.Thread(target=_run_test_process_in_background)
            self.test_thread.start()
            self.save_config()
            #self.btn_start.setText('Stop')
       

    def bt_device_check(self):
        #checking the bt device existed, like headset, mouse
        headset = BluetoothControl.find_headset()
        self.led_headset.setText(headset)
        self.b_config.headset = headset

    def advance_setting(self):
        self.settings_window = AdvanceSetting(self.b_config)
        self.settings_window.setting_changed.connect(self.apply_setting)
        self.settings_window.show()

    def apply_setting(self, basic_config:Basic_Config):
        self.b_config = basic_config
    
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
        if self.b_config.do_mouse_flag:
            self.ck_btn_mouse.setChecked(True)
        if self.b_config.do_headset_output_flag:
            self.ck_btn_h_output.setChecked(True)
        if self.b_config.do_headset_input_flag:
            self.ck_btn_h_input.setChecked(True)

        self.slider_test_times.setValue(self.b_config.test_times)
    
    def update_slider_value(self,value_name,value):
        match value_name:
            case "test_times":
                self.value_tts.setText(str(value))
                self.b_config.test_times = value

    def update_cell(self, row, col, text):
        item = self.task_schedule_model.item(row, col)
        if item:
            item.setText(text)

    def closeEvent(self, event):
        self.save_config()
        event.accept()  # Accept the close event
    
    def save_config(self):
        # Convert dataclass to dictionary
        config_dict = asdict(self.b_config)
        # Save to YAML
        with open("config_basic.yaml", "w") as f:
            yaml.dump(config_dict, f)
        print("Configuration saved to yaml")

            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    b_config = test_process.load_basic_config("config_basic.yaml")
    window = BTTestApp(b_config=b_config)
    window.show()
    sys.exit(app.exec_())
