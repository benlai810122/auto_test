from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QCheckBox,QLineEdit, QTableView,QSlider,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,QRadioButton
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem,QTextCursor, QColor, QBrush, QFont
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
from datetime import datetime



class LogSignal(QObject):
    log = pyqtSignal(str)
    error = pyqtSignal(str)
    cell = pyqtSignal(int,int,str)
    process = pyqtSignal(int,int)
    save_report = pyqtSignal(int,int)

class BTTestApp(QWidget):
    
    b_config:Basic_Config = None
    task_schedule:list[str] = []
    test_thread:threading = None
    power_states_clicking:str = ""
    test_case_clicking:str = ""
    thread_stop_flag = False

    def __init__(self, b_config:Basic_Config):
        super().__init__()
        self.b_config = b_config
        self.setWindowTitle("User Experience Auto Test")
        self.setGeometry(100, 100, 800, 1000)
        self.init_ui()
        self.bt_device_check()
        self.ui_renew()
        self.log_signal = LogSignal()
        self.log_signal.log.connect(self.log_to_ui)
        self.log_signal.cell.connect(self.update_cell)
        self.log_signal.error.connect(self.error_to_ui)
        self.log_signal.process.connect(self.update_process)
        self.log_signal.save_report.connect(self.save_report)
       

    def init_ui(self):
        layout = QVBoxLayout()

        # --- setting ---
        self.setting_group = QGroupBox("Setting")
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
        self.setting_group.setLayout(setting_layout)


        # --- Device Selection ---
        self.device_group = QGroupBox("Device Selection")
        device_layout = QFormLayout()

        self.led_headset = QLineEdit()
        self.led_headset.setReadOnly(True)

        self.led_mouse = QLineEdit()
        self.led_mouse.setReadOnly(True)

        device_layout.addRow("Headset:", self.led_headset)
        device_layout.addRow("Mouse:", self.led_mouse)
        self.device_group.setLayout(device_layout)

        # --- Power states Selection ---
        self.power_states_group = QGroupBox("DUT Power States")
        power_states_layout = QHBoxLayout()

        self.rbtn_idle = QRadioButton("IDLE")
        self.rbtn_ms = QRadioButton("MS")
        self.rbtn_s4 = QRadioButton("S4")
        self.btn_ps_add = QPushButton("Add")

        self.rbtn_idle.clicked.connect(partial(self.power_states_setting,"Idle"))
        self.rbtn_ms.clicked.connect(partial(self.power_states_setting,"MS"))
        self.rbtn_s4.clicked.connect(partial(self.power_states_setting,"S4"))
        self.btn_ps_add.clicked.connect(partial(self.task_schedule_setting,"ps_add"))
        self.btn_ps_add.setMaximumWidth(100)

        power_states_layout.addWidget(self.rbtn_idle)
        power_states_layout.addWidget(self.rbtn_ms)
        power_states_layout.addWidget(self.rbtn_s4)
        power_states_layout.addWidget(self.btn_ps_add)
        self.power_states_group.setLayout(power_states_layout)

        # --- Test Case Selection ---
        self.test_case_group = QGroupBox("Test Case Selection")
        test_layout = QVBoxLayout()


        func_level_1 =  QHBoxLayout()
        self.ck_btn_mouse = QRadioButton("Mouse Function")
        self.ck_btn_h_input = QRadioButton("Headset Input")
        self.ck_btn_h_output = QRadioButton("Headset Output")
        self.ck_btn_mouse.clicked.connect(partial(self.test_case_setting,'Mouse_function'))
        self.ck_btn_h_input.clicked.connect(partial(self.test_case_setting,'Headset_input'))
        self.ck_btn_h_output.clicked.connect(partial(self.test_case_setting,'Headset_output'))
        func_level_1.addWidget(self.ck_btn_mouse)
        func_level_1.addWidget(self.ck_btn_h_input)
        func_level_1.addWidget(self.ck_btn_h_output)

        func_level_2 =  QHBoxLayout()
        self.ck_btn_h_init = QRadioButton("Headset Init")
        self.ck_btn_h_del = QRadioButton("Headset Del")
        self.ck_btn_m_random = QRadioButton("Mouse Random")
        self.ck_btn_h_init.clicked.connect(partial(self.test_case_setting,'Headset_init'))
        self.ck_btn_h_del.clicked.connect(partial(self.test_case_setting,'Headset_del'))
        self.ck_btn_m_random.clicked.connect(partial(self.test_case_setting,'Mouse_random'))
        func_level_2.addWidget(self.ck_btn_h_init)
        func_level_2.addWidget(self.ck_btn_h_del)
        func_level_2.addWidget(self.ck_btn_m_random)

        func_level_3 =  QHBoxLayout()
        self.ck_btn_h_m_function = QRadioButton("Mouse_function + Headset output")
        self.empty_1 = QLabel("")
        self.empty_2 = QLabel("")
        self.ck_btn_h_m_function.clicked.connect(partial(self.test_case_setting,'Mouse_function + Headset output'))
        func_level_3.addWidget(self.ck_btn_h_m_function)
        func_level_3.addWidget(self.empty_1)
        func_level_3.addWidget(self.empty_2)


        self.btn_tc_add = QPushButton("Add")
        self.btn_tc_add.clicked.connect(partial(self.task_schedule_setting,"tc_add"))
        self.btn_tc_add.setMaximumWidth(100)
        
        test_layout.addLayout(func_level_1)
        test_layout.addLayout(func_level_2)
        test_layout.addLayout(func_level_3)

        test_layout.addWidget(self.btn_tc_add)
        self.test_case_group.setLayout(test_layout)

        # --- Task schedule table ---
        self.task_schedule_group = QGroupBox("Task schedule")
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

        task_setting_laylout.addWidget(self.lab_test_times)
        task_setting_laylout.addWidget(self.slider_test_times)
        task_setting_laylout.addWidget(self.value_tts)

        self.lab_test_process = QLabel("Test Cycles:             Pass:         Fail:    ")
        self.lab_test_process.setStyleSheet(
        """
            QLabel {
                color: white;                /* Text color */
                background-color: black;     /* Background */
                font-size: 16px;              /* Font size */
                font-weight: bold;            /* Bold text */
                border: 1px solid gray;       /* Border */
                padding: 4px;                 /* Inner spacing */
            }
        """)
    
        self.btn_delet = QPushButton("Delet")
        self.btn_delet.clicked.connect(partial(self.task_schedule_setting,"delet"))
        self.btn_delet.setMaximumWidth(100)

        self.task_schedule_model = QStandardItemModel(0, 2) 
        self.task_schedule_model.setHorizontalHeaderLabels(["Test Case","Status"])
        table_view = QTableView()
        table_view.setModel(self.task_schedule_model)
        table_view.setColumnWidth(0, 500)
        task_schedule_layout.addLayout(task_setting_laylout)
        task_schedule_layout.addWidget(self.lab_test_process)
        task_schedule_layout.addWidget(table_view)
        task_schedule_layout.addWidget(self.btn_delet)
        self.task_schedule_group.setLayout(task_schedule_layout)

        # --- Log Output ---

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        font = QFont("Arial", 10)  # font family, size
        self.log_output.setFont(font)

        # --- Error message ---
        self.error_message = QTextEdit()
        self.error_message.setReadOnly(True)
        self.error_message.setMaximumHeight(80)
        self.error_message.setTextColor(QColor("red"))
        font = QFont("Arial", 12)  # font family, size
        self.error_message.setFont(font)


        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.run_test)
        self.btn_quit = QPushButton("Quit")
        self.btn_quit.clicked.connect(self.close)
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_quit)

        # --- Combine All Layouts ---
        layout.addWidget(self.setting_group)
        layout.addWidget(self.device_group)
        layout.addWidget(self.power_states_group)
        layout.addWidget(self.test_case_group)
        layout.addWidget(self.task_schedule_group)
        layout.addWidget(QLabel("Test Progress:"))
        layout.addWidget(self.log_output)
        layout.addWidget(QLabel("Error Message:"))
        layout.addWidget(self.error_message)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def task_schedule_setting(self, name:str):
        match name:
            case "ps_add":
                # power states:
                if self.power_states_clicking: 
                    self.task_schedule.append(self.power_states_clicking)
                    new_row = [QStandardItem(self.power_states_clicking), QStandardItem("")]
                    self.task_schedule_model.appendRow(new_row)
            case "tc_add":
                # power states:
                if self.test_case_clicking:
                    self.task_schedule.append(self.test_case_clicking)
                    new_row = [QStandardItem(self.test_case_clicking), QStandardItem("")]
                    self.task_schedule_model.appendRow(new_row)
            case "delet": 
                row_count = self.task_schedule_model.rowCount()
                if row_count:
                    self.task_schedule_model.removeRow(row_count - 1)
                    self.task_schedule.pop()

    def power_states_setting(self, power_states:str):
        #setting the power states
        self.power_states_clicking = power_states
    
    def save_report(self, test_cycle:int, test_fail_times:int):
        #save_report and recover ui
        test_process.save_report(self.b_config,test_cycle,test_fail_times,self.error_message.toPlainText())
        self.btn_start.setText("Start")
        self.enable_all_item()
       

    def test_case_setting(self, test_case:str):
        #setting the test case
        self.test_case_clicking = test_case

    def log_to_ui(self,msg:str):
        # Run test logic and log output to UI and log file
        #current_text = self.log_output.toPlainText()
        #updated_text = f"{msg}\n{current_text}"
        current_time = datetime.now()
        msg = f"[{current_time}] {msg}"
        self.log_output.append(msg)
        self.log_output.moveCursor(QTextCursor.End)
        logger.info(msg)

    def error_to_ui(self,msg:str):
        current_time = datetime.now()
        msg = f"[{current_time}] {msg}"
        self.error_message.append(msg)
        self.error_message.moveCursor(QTextCursor.End)
        logger.error(msg)

    def serial_port_check(self):
        #check arduino board existed 
        self.log_output.clear()  # Clear previous logs
        test_process.get_arduino_port(port=self.b_config.target_port_desc, log_callback=self.log_to_ui)

    def run_test(self):
        #run the main test process
        def _run_test_process_in_background():
            self.log_signal.log.emit("Start testing...")
            test_fail_times = 0
            test_cycle = 0
            for cycle in range(self.b_config.test_times):
                row = 0
                for test_case in self.task_schedule:
                    if self.thread_stop_flag:
                        break
                    self.log_signal.cell.emit(row,1,"running...")
                    test_result = test_process.run_test(test_case,self.b_config,self.log_signal.log.emit)
                    if test_result:
                        self.log_signal.cell.emit(row,1,"Pass")
                    else:
                        error_message =  f"test case: {test_case} item:{row+1} cycles:{cycle}"
                        self.log_signal.cell.emit(row,1,"Fail")
                        self.log_signal.error.emit(error_message)
                        test_fail_times+=1
                    row+=1
                test_cycle = cycle
                # stop thread if stop btn have been clicked
                if self.thread_stop_flag:
                    break
                #update process lab
                self.log_signal.process.emit(cycle+1,test_fail_times)
                #renew the status for another run:
                for i in range(row):
                    self.log_signal.cell.emit(i,1,"")
                
            self.log_signal.log.emit("Test Finish! generate final report...")
            self.log_signal.save_report.emit(test_cycle+1,test_fail_times)
            self.log_signal.log.emit("Final report is ready!")

            

        if self.btn_start.text() == "Start":
            self.thread_stop_flag = False
            self.test_thread = threading.Thread(target=_run_test_process_in_background)
            self.test_thread.start()
            self.save_config()
            self.btn_start.setText('Stop')
            self.disable_all_item()

        elif self.btn_start.text() == "Stop":
            self.thread_stop_flag = True
            self.log_to_ui("Test terminate!")
            self.btn_start.setText('Start')
            self.enable_all_item()

    def disable_all_item(self):
        self.power_states_group.setDisabled(True)
        self.setting_group.setDisabled(True)
        self.device_group.setDisabled(True)
        self.test_case_group.setDisabled(True)
        self.task_schedule_group.setDisabled(True)
    def enable_all_item(self):
        self.power_states_group.setDisabled(False)
        self.setting_group.setDisabled(False)
        self.device_group.setDisabled(False)
        self.test_case_group.setDisabled(False)
        self.task_schedule_group.setDisabled(False)


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
        self.slider_test_times.setValue(self.b_config.test_times)
        #task schedule init
        self.task_schedule = self.b_config.task_schedule.split(',')
        for test_item in self.task_schedule:
            if test_item:
                new_row = [QStandardItem(test_item), QStandardItem("")]
                self.task_schedule_model.appendRow(new_row)

    
    def update_slider_value(self,value_name,value):
        match value_name:
            case "test_times":
                self.value_tts.setText(str(value))
                self.b_config.test_times = value

    def update_cell(self, row, col, text):
        item = self.task_schedule_model.item(row, col)
        if item:
            item.setText(text)
            if text == 'Pass':
                item.setForeground(QBrush(QColor("green")))
            elif text == 'Fail':
                item.setForeground(QBrush(QColor("red")))
            elif text == 'running...':
                item.setForeground(QBrush(QColor("black")))

    def update_process(self, cycles:int, fail_times:int):
        self.lab_test_process.setText(f"Test Cycles: {cycles}            Pass: {cycles-fail_times}         Fail: {fail_times}")


    def closeEvent(self, event):
        self.thread_stop_flag = True
        self.save_config()
        event.accept()  # Accept the close event
    
    def save_config(self):
        #update task schedule
        self.b_config.task_schedule = ""
        for test_item in self.task_schedule:
            if test_item != "":
                self.b_config.task_schedule += test_item + ','
        self.b_config.task_schedule = self.b_config.task_schedule[:-1]

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
