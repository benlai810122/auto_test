from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QTableView,
    QSlider,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QRadioButton,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QTextCursor,
    QColor,
    QBrush,
    QFont,
)
from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtCore import pyqtSignal, QObject
import sys
import test_process
from test_process import Basic_Config
from test_process import Power_States
from test_process import Test_case
from utils import log as logger
from bt_control import BluetoothControl
from ui_adv_setting import AdvanceSetting
from functools import partial
import threading
import copy
import yaml
from dataclasses import asdict
from datetime import datetime
import latency_analyze as la
from ui_database_setting import DataBase_Data_setting
import database_manager
from database_manager import Database_data
import time


class LogSignal(QObject):
    log = pyqtSignal(str, bool)
    error = pyqtSignal(str)
    cell = pyqtSignal(int, int, str)
    process = pyqtSignal(int, int)
    save_report = pyqtSignal(int, int, int)
    enable = pyqtSignal()
    set_stutas = pyqtSignal(int, int)


class BTTestApp(QWidget):

    b_config: Basic_Config = None
    task_schedule: list[str] = []
    test_thread: threading = None
    power_states_clicking: str = ""
    test_case_clicking: str = ""
    thread_stop_flag = False

    def __init__(self, b_config: Basic_Config, database_data: Database_data):
        super().__init__()
        self.b_config = b_config
        self.database_data = database_data
        self.setWindowTitle("Intel User Experience Auto Test")
        self.setGeometry(100, 100, 1600, 1200)
        self.init_ui()
        self.bt_device_check()
        self.serial_port_check()
        self.ui_renew()
        self.log_signal = LogSignal()
        self.log_signal.log.connect(self.log_to_ui)
        self.log_signal.cell.connect(self.update_cell)
        self.log_signal.error.connect(self.error_to_ui)
        self.log_signal.process.connect(self.update_process)
        self.log_signal.save_report.connect(self.save_report)
        self.log_signal.enable.connect(self.enable_all_item)
        self.log_signal.set_stutas.connect(self.set_stutas)

    def init_ui(self):

        self.setStyleSheet(
            """
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
            QTableView {
                gridline-color: #555;
                background-color: #f9f9f9;
                alternate-background-color: #eaeaea;
                border: 1px solid #ccc;
                font-family: Segoe UI;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 4px;
                border: 1px solid #333;
                font-weight: bold;
            }
        """
        )

        def make_title(text):
            label = QLabel(text)
            label.setStyleSheet("font-size: 16px; font-weight: bold;")
            return label

        layout_main = QHBoxLayout()
        layout_1 = QVBoxLayout()
        layout_2 = QVBoxLayout()

        # --- setting ---
        self.setting_group = QGroupBox("Setting")
        setting_layout = QHBoxLayout()
        self.btn_ardu_check = QPushButton("Arduino Check")
        self.btn_bt_check = QPushButton("Peripheral Check")
        self.btn_advance_setting = QPushButton("Advanced Setting")
        self.btn_database_setting = QPushButton("Database Setting")

        self.btn_ardu_check.clicked.connect(self.serial_port_check)
        self.btn_bt_check.clicked.connect(self.bt_device_check)
        self.btn_advance_setting.clicked.connect(self.advance_setting)
        self.btn_database_setting.clicked.connect(self.database_setting)
        setting_layout.addWidget(self.btn_ardu_check)
        setting_layout.addWidget(self.btn_bt_check)
        setting_layout.addWidget(self.btn_advance_setting)
        setting_layout.addWidget(self.btn_database_setting)
        self.setting_group.setLayout(setting_layout)

        # --- Device Selection ---
        self.device_group = QGroupBox("Device")
        device_layout = QFormLayout()

        self.led_headset = QLineEdit()
        self.led_headset.setReadOnly(True)

        self.led_mouse = QLineEdit()
        self.led_mouse.setReadOnly(True)

        self.led_keyboard = QLineEdit()
        self.led_keyboard.setReadOnly(True)

        device_layout.addRow(make_title("Headset:"), self.led_headset)
        device_layout.addRow(make_title("Mouse:"), self.led_mouse)
        device_layout.addRow(make_title("Keyboard:"), self.led_keyboard)
        self.device_group.setLayout(device_layout)

        # --- Power states Selection ---
        self.power_states_group = QGroupBox("DUT Power States")
        power_states_layout = QVBoxLayout()

        layout_P_1 = QHBoxLayout()
        self.rbtn_idle = QRadioButton("IDLE")
        self.rbtn_ms = QRadioButton("Modern Standby (MS)")
        self.rbtn_s4 = QRadioButton("Hibernation (S4)")
        self.btn_ps_add = QPushButton("Add")

        self.rbtn_idle.clicked.connect(
            partial(self.power_states_setting, Test_case.Idle.value)
        )
        self.rbtn_ms.clicked.connect(
            partial(self.power_states_setting, Test_case.MS.value)
        )
        self.rbtn_s4.clicked.connect(
            partial(self.power_states_setting, Test_case.S4.value)
        )
        self.btn_ps_add.clicked.connect(partial(self.task_schedule_setting, "ps_add"))
        self.btn_ps_add.setMaximumWidth(100)

        layout_P_1.addWidget(self.rbtn_idle)
        layout_P_1.addWidget(self.rbtn_ms)
        layout_P_1.addWidget(self.rbtn_s4)

        power_states_layout.addLayout(layout_P_1)
        power_states_layout.addWidget(self.btn_ps_add)
        self.power_states_group.setLayout(power_states_layout)

        # --- Test Case Selection ---
        self.test_case_group = QGroupBox("Test Case Selection")
        test_layout = QVBoxLayout()

        func_level_1 = QHBoxLayout()
        self.ck_btn_mouse = QRadioButton("Mouse Function Check")
        self.ck_btn_m_random = QRadioButton("Mouse Random Click")
        self.ck_btn_ml = QRadioButton("Mouse Latency Test")
        self.empty1_4 = QLabel("")

        self.ck_btn_mouse.clicked.connect(
            partial(self.test_case_setting, Test_case.Mouse_function.value)
        )
        self.ck_btn_m_random.clicked.connect(
            partial(self.test_case_setting, Test_case.Mouse_random.value)
        )
        self.ck_btn_ml.clicked.connect(
            partial(self.test_case_setting, Test_case.Mouse_latency.value)
        )
        func_level_1.addWidget(self.ck_btn_mouse)
        func_level_1.addWidget(self.ck_btn_m_random)
        func_level_1.addWidget(self.ck_btn_ml)
        func_level_1.addWidget(self.empty1_4)

        func_level_2 = QHBoxLayout()
        self.ck_btn_h_input = QRadioButton("Headset Mic Check")
        self.ck_btn_h_output = QRadioButton("Headset Output Check")
        self.ck_btn_h_init = QRadioButton("Headset Initialization")
        self.ck_btn_h_del = QRadioButton("Headset Restore")
        self.ck_btn_h_input.clicked.connect(
            partial(self.test_case_setting, Test_case.Headset_input.value)
        )
        self.ck_btn_h_output.clicked.connect(
            partial(self.test_case_setting, Test_case.Headset_output.value)
        )
        self.ck_btn_h_init.clicked.connect(
            partial(self.test_case_setting, Test_case.Headset_init.value)
        )
        self.ck_btn_h_del.clicked.connect(
            partial(self.test_case_setting, Test_case.Headset_del.value)
        )
        func_level_2.addWidget(self.ck_btn_h_input)
        func_level_2.addWidget(self.ck_btn_h_output)
        func_level_2.addWidget(self.ck_btn_h_init)
        func_level_2.addWidget(self.ck_btn_h_del)

        func_level_3 = QHBoxLayout()
        self.ck_btn_k_function = QRadioButton("Keyboard Function Check")
        self.ck_btn_kr = QRadioButton("Keyboard Random Click")
        self.ck_btn_kl = QRadioButton("Keyboard Latency Test")

        self.emtpy3_4 = QLabel("")
        self.ck_btn_k_function.clicked.connect(
            partial(self.test_case_setting, Test_case.keyboard_function.value)
        )
        self.ck_btn_kr.clicked.connect(
            partial(self.test_case_setting, Test_case.Keyboard_random.value)
        )
        self.ck_btn_kl.clicked.connect(
            partial(self.test_case_setting, Test_case.keyboard_latency.value)
        )
        func_level_3.addWidget(self.ck_btn_k_function)
        func_level_3.addWidget(self.ck_btn_kr)
        func_level_3.addWidget(self.ck_btn_kl)
        func_level_3.addWidget(self.emtpy3_4)

        func_level_4 = QHBoxLayout()
        self.ck_btn_env_init = QRadioButton("Environment Initialization")
        self.ck_btn_env_restore = QRadioButton("Environment Restore")
        self.emtpy4_3 = QLabel("")
        self.emtpy4_4 = QLabel("")
        self.ck_btn_env_init.clicked.connect(
            partial(self.test_case_setting, Test_case.Environment_init.value)
        )
        self.ck_btn_env_restore.clicked.connect(
            partial(self.test_case_setting, Test_case.Environment_restore.value)
        )
        func_level_4.addWidget(self.ck_btn_env_init)
        func_level_4.addWidget(self.ck_btn_env_restore)
        func_level_4.addWidget(self.emtpy4_3)
        func_level_4.addWidget(self.emtpy4_4)

        self.btn_tc_add = QPushButton("Add")
        self.btn_tc_add.clicked.connect(partial(self.task_schedule_setting, "tc_add"))
        self.btn_tc_add.setMaximumWidth(100)

        test_layout.addLayout(func_level_1)
        test_layout.addLayout(func_level_2)
        test_layout.addLayout(func_level_3)
        test_layout.addLayout(func_level_4)
        test_layout.addWidget(self.btn_tc_add)
        self.test_case_group.setLayout(test_layout)

        # --- state label ---
        self.status_label = StatusLabel()

        # --- Task schedule table ---
        self.task_schedule_group = QGroupBox("Task schedule")
        task_schedule_layout = QVBoxLayout()

        task_setting_laylout = QHBoxLayout()
        self.lab_test_times = QLabel("Test times:")
        self.value_tts = QLabel("1")  # Default value
        self.value_tts.setAlignment(Qt.AlignCenter)
        self.value_tts.setStyleSheet("font-size: 16px;")
        self.slider_test_times = QSlider(Qt.Horizontal)
        self.slider_test_times.setMinimum(1)
        self.slider_test_times.setMaximum(1000)
        self.slider_test_times.setValue(1)
        self.slider_test_times.setTickInterval(1)
        self.slider_test_times.setTickPosition(QSlider.TicksBelow)
        self.slider_test_times.valueChanged.connect(
            partial(self.update_slider_value, "test_times")
        )

        task_setting_laylout.addWidget(self.lab_test_times)
        task_setting_laylout.addWidget(self.slider_test_times)
        task_setting_laylout.addWidget(self.value_tts)

        self.lab_test_process = QLabel(
            "Test Cycles:             Pass:         Fail:    "
        )
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
        """
        )

        self.btn_delet = QPushButton("undo")
        self.btn_delet.clicked.connect(partial(self.task_schedule_setting, "delet"))
        self.btn_delet.setMaximumWidth(200)
        self.btn_delet.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))

        self.task_schedule_model = QStandardItemModel(0, 2)
        self.task_schedule_model.setHorizontalHeaderLabels(["Test Case", "Status"])

        table_view = QTableView()
        table_view.setModel(self.task_schedule_model)
        table_view.setColumnWidth(0, 400)

        table_view.setAlternatingRowColors(True)
        table_view.setShowGrid(False)
        task_schedule_layout.addLayout(task_setting_laylout)
        task_schedule_layout.addWidget(self.lab_test_process)
        task_schedule_layout.addWidget(table_view)
        task_schedule_layout.addWidget(self.btn_delet)
        self.task_schedule_group.setLayout(task_schedule_layout)

        # --- summary ---
        self.summary_group = QGroupBox("Summary")
        layout = QFormLayout()
        self.label_total = QLabel("0 / 0")
        self.label_pass = QLabel("0")
        self.label_fail = QLabel("0")
        self.label_first_fail = QLabel("-")
        self.label_keyboard_latency = QLabel("-")
        self.label_mouse_latency = QLabel("-")

        # Apply styles
        self.label_total.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.label_pass.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: green;"
        )
        self.label_fail.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")
        self.label_first_fail.setStyleSheet("font-size: 16px; color: blue;")
        self.label_keyboard_latency.setStyleSheet("font-size: 16px;")
        self.label_mouse_latency.setStyleSheet("font-size: 16px;")

        layout.addRow(make_title("Total Tests:"), self.label_total)
        layout.addRow(make_title("✅ Pass:"), self.label_pass)
        layout.addRow(make_title("❌ Fail:"), self.label_fail)
        layout.addRow(make_title("Earliest Fail Time:"), self.label_first_fail)
        layout.addRow(
            make_title("Keyboard average Latency:"), self.label_keyboard_latency
        )
        layout.addRow(make_title("Mouse average Latency:"), self.label_mouse_latency)

        self.summary_group.setLayout(layout)

        # --- Log Output ---

        self.log_group = QGroupBox("Message")
        group_layout = QVBoxLayout()

        # log box
        self.log_title = make_title("Test Process:")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        font = QFont("Arial", 10)  # font family, size
        self.log_output.setFont(font)

        # Error message
        self.error_message_title = make_title("Error Message:")
        self.error_message = QTextEdit()
        self.error_message.setReadOnly(True)
        self.error_message.setMaximumHeight(150)
        self.error_message.setTextColor(QColor("red"))
        font = QFont("Arial", 12)  # font family, size
        self.error_message.setFont(font)

        group_layout.addWidget(self.log_title)
        group_layout.addWidget(self.log_output)
        group_layout.addWidget(self.error_message_title)
        group_layout.addWidget(self.error_message)
        self.log_group.setLayout(group_layout)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.run_test)
        self.btn_quit = QPushButton("Quit")
        self.btn_quit.clicked.connect(self.close)

        self.btn_start.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_quit.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_quit)

        # --- Combine All Layouts ---
        layout_1.addWidget(self.status_label)
        layout_1.addWidget(self.device_group)
        layout_1.addWidget(self.power_states_group)
        layout_1.addWidget(self.test_case_group)
        layout_1.addWidget(self.log_group)
        layout_1.addLayout(button_layout)

        layout_2.addWidget(self.setting_group)
        layout_2.addWidget(self.task_schedule_group)
        layout_2.addWidget(self.summary_group)

        layout_main.addLayout(layout_1)
        layout_main.addLayout(layout_2)
        self.setLayout(layout_main)

    def task_schedule_setting(self, name: str):
        match name:
            case "ps_add":
                # power states:
                if self.power_states_clicking:
                    self.task_schedule.append(self.power_states_clicking)
                    item_case = QStandardItem(self.power_states_clicking)
                    item_case.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font
                    state = QStandardItem("")
                    state.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font
                    new_row = [item_case, state]
                    self.task_schedule_model.appendRow(new_row)
            case "tc_add":
                # power states:
                if self.test_case_clicking:
                    self.task_schedule.append(self.test_case_clicking)
                    item_case = QStandardItem(self.test_case_clicking)
                    item_case.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font
                    state = QStandardItem("")
                    state.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font
                    new_row = [item_case, state]
                    self.task_schedule_model.appendRow(new_row)
            case "delet":
                row_count = self.task_schedule_model.rowCount()
                if row_count:
                    self.task_schedule_model.removeRow(row_count - 1)
                    self.task_schedule.pop()

    def power_states_setting(self, power_states: str):
        # setting the power states
        self.power_states_clicking = power_states

    def save_report(self, test_cycle: int, test_fail_times: int, duration: int):
        # update database data
        self.database_data.date = datetime.now()
        self.database_data.scenario = self.b_config.task_schedule
        self.database_data.fail_cycles = test_fail_times
        self.database_data.cycles = test_cycle
        self.database_data.result = "Pass" if not test_fail_times else "Fail"
        self.database_data.duration = duration

        # save_report after test finish
        test_process.save_report(
            self.b_config,
            self.database_data,
            test_cycle,
            test_fail_times,
            self.error_message.toPlainText(),
        )

    def set_stutas(self, test_cycle: int, test_fail_times: int):
        # set the ui state after test finish
        # status label
        if test_fail_times:
            self.status_label.set_state("FAIL")
        else:
            self.status_label.set_state("PASS")

        # summary group
        total_test_time = f"{test_cycle}/{self.b_config.test_times} cycles"
        pass_times = f"{test_cycle-test_fail_times}"
        fail_times = f"{test_fail_times}"

        message = self.error_message.toPlainText()  # get all text
        lines = message.splitlines()  # split into lines
        first_fail_message = lines[0] if lines else ""  # safe check

        message = self.log_output.toPlainText()
        mouse_aver = la.latency_analyze("mouse", message)
        keyboard_aver = la.latency_analyze("keyboard", message)

        self.label_total.setText(total_test_time)
        self.label_pass.setText(pass_times)
        self.label_fail.setText(fail_times)
        self.label_first_fail.setText(first_fail_message)
        if keyboard_aver:
            self.label_keyboard_latency.setText(f"{keyboard_aver} ms")
        else:
            self.label_keyboard_latency.setText("-")

        if mouse_aver:
            self.label_mouse_latency.setText(f"{mouse_aver} ms")
        else:
            self.label_mouse_latency.setText("-")

        #

    def test_case_setting(self, test_case: str):
        # setting the test case
        self.test_case_clicking = test_case

    def log_to_ui(self, msg: str, is_bold: bool = False):
        # Run test logic and log output to UI and log file
        # current_text = self.log_output.toPlainText()
        # updated_text = f"{msg}\n{current_text}"
        current_time = datetime.now()
        if is_bold:
            msg = f'<span style="font-weight:bold; color:navy;">[{current_time}] {msg}</span>'
        else:
            msg = f'<span style="font-weight:normal; color:black;">[{current_time}] {msg}</span>'
        self.log_output.append(msg)
        self.log_output.moveCursor(QTextCursor.End)
        logger.info(msg)

    def error_to_ui(self, msg: str):
        current_time = datetime.now()
        msg = f"[{current_time}] {msg}"
        self.error_message.append(msg)
        self.error_message.moveCursor(QTextCursor.End)
        logger.error(msg)

    def serial_port_check(self):
        # check arduino board existed
        self.log_output.clear()  # Clear previous logs
        self.b_config.com = test_process.get_arduino_port(
            port=self.b_config.target_port_desc, log_callback=self.log_to_ui
        )

    def run_test(self):
        # run the main test process
        def _run_test_process_in_background():
            self.log_signal.log.emit("Start testing...", False)
            test_fail_times = 0
            test_cycle = 0
            self.log_signal.process.emit(0, 0)
            test_fail_flag = False
            test_fail_continue_times = 0
            start = time.perf_counter()
            for cycle in range(self.b_config.test_times):
                row = 0
                for test_case in self.task_schedule:
                    if self.thread_stop_flag:
                        break
                    self.log_signal.cell.emit(row, 1, "running...")
                    test_result = test_process.run_test(
                        test_case, self.b_config, self.log_signal.log.emit
                    )
                    if test_result:
                        self.log_signal.cell.emit(row, 1, "Pass")
                    else:
                        error_message = (
                            f"test case: {test_case} item:{row+1} cycles:{cycle}"
                        )
                        self.log_signal.cell.emit(row, 1, "Fail")
                        self.log_signal.error.emit(error_message)
                        test_fail_flag = True
                    row += 1

                test_cycle = cycle

                if test_fail_flag:
                    test_fail_continue_times += 1
                    test_fail_times += 1
                    test_fail_flag = False
                else:
                    test_fail_continue_times = 0

                # update process lab
                self.log_signal.process.emit(cycle + 1, test_fail_times)

                # renew the status for another run:
                for i in range(row):
                    self.log_signal.cell.emit(i, 1, "")

                # stop thread if stop btn have been clicked
                if self.thread_stop_flag:
                    break

                # if out of continue fail range, stop testing
                if test_fail_continue_times >= self.b_config.continue_fail_limit:
                    self.log_signal.log.emit("Stop testing!", True)
                    self.log_signal.error.emit(
                        "out of maxium continue fail range, stop testing!"
                    )
                    break

            end = time.perf_counter()
            self.log_signal.log.emit("Test Finish! generate final report...", True)
            self.log_signal.save_report.emit(
                test_cycle + 1, test_fail_times, int(end - start)
            )
            self.log_signal.log.emit(
                "Final report is ready and dump to report folder!", True
            )
            self.log_signal.set_stutas.emit(test_cycle + 1, test_fail_times)
            self.log_signal.enable.emit()

        if self.btn_start.text() == "Start":
            self.thread_stop_flag = False
            self.error_message.setPlainText("")
            self.log_output.setPlainText("")
            self.test_thread = threading.Thread(target=_run_test_process_in_background)
            self.test_thread.start()
            self.save_config()
            self.btn_start.setText("Stop")
            self.btn_start.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.disable_all_item()
            self.status_label.set_state("RUNNING")

        elif self.btn_start.text() == "Stop":
            self.thread_stop_flag = True
            self.log_to_ui("Test terminate!")
            self.btn_start.setText("waiting...")
            self.btn_start.setDisabled(True)
            self.btn_quit.setDisabled(True)
            self.status_label.set_state("WAITING")

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
        self.btn_quit.setDisabled(False)
        self.btn_start.setDisabled(False)
        self.task_schedule_group.setDisabled(False)
        self.btn_start.setText("Start")
        self.btn_start.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def bt_device_check(self):
        # checking the bt device existed, like headset, mouse
        headset = BluetoothControl.find_headset()
        mouse = BluetoothControl.find_mouse_keyboard("Mouse")
        keyboard = BluetoothControl.find_mouse_keyboard("Keyboard")
        self.led_headset.setText(headset)
        self.led_mouse.setText(mouse)
        self.led_keyboard.setText(keyboard)
        self.b_config.headset = headset
        # database
        self.database_data.mouse = mouse
        self.database_data.keyboard = keyboard
        self.database_data.headset = headset

    def advance_setting(self):
        self.settings_window = AdvanceSetting(self.b_config)
        self.settings_window.setting_changed.connect(self.apply_setting)
        self.settings_window.show()

    def database_setting(self):

        self.database_window = DataBase_Data_setting(
            "database_data.xlsx", self.database_data
        )
        self.database_window.setting_changed.connect(self.apply_databaseSetting)
        self.database_window.show()

    def apply_setting(self, basic_config: Basic_Config):
        self.b_config = basic_config

    def apply_databaseSetting(self, database_data: Database_data):
        self.database_data = database_data

    def ui_renew(self):
        self.slider_test_times.setValue(self.b_config.test_times)
        # task schedule init
        self.task_schedule = self.b_config.task_schedule.split(",")
        for test_item in self.task_schedule:
            if test_item:
                item_case = QStandardItem(test_item)
                item_case.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font

                state = QStandardItem("")
                state.setFont(QFont("Arial", 12, QFont.Bold))  # Bold font

                new_row = [item_case, state]
                self.task_schedule_model.appendRow(new_row)

    def update_slider_value(self, value_name, value):
        match value_name:
            case "test_times":
                self.value_tts.setText(str(value))
                self.b_config.test_times = value

    def update_cell(self, row, col, text):
        item = self.task_schedule_model.item(row, col)
        if item:
            item.setText(text)
            if text == "Pass":
                item.setForeground(QBrush(QColor("green")))
            elif text == "Fail":
                item.setForeground(QBrush(QColor("red")))
            elif text == "running...":
                item.setForeground(QBrush(QColor("black")))

    def update_process(self, cycles: int, fail_times: int):
        self.lab_test_process.setText(
            f"Test Cycles: {cycles}            Pass: {cycles-fail_times}         Fail: {fail_times}"
        )

    def closeEvent(self, event):
        self.thread_stop_flag = True
        self.save_config()
        self.save_database_data()
        event.accept()  # Accept the close event

    def save_config(self):
        # update task schedule
        self.b_config.task_schedule = ""
        for test_item in self.task_schedule:
            if test_item != "":
                self.b_config.task_schedule += test_item + ","
        self.b_config.task_schedule = self.b_config.task_schedule[:-1]

        # Convert dataclass to dictionary
        config_dict = asdict(self.b_config)
        # Save to YAML
        with open("config_basic.yaml", "w") as f:
            yaml.dump(config_dict, f)
        print("Configuration saved to yaml")

    def save_database_data(self):
        # Convert dataclass to dictionary
        database_dict = asdict(self.database_data)
        # Save to YAML
        with open("database_data.yaml", "w") as f:
            yaml.dump(database_dict, f)
        print("database_data saved to yaml")


class StatusLabel(QLabel):

    def __init__(self, text="Intel"):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(100)

        # Font
        font = QFont("Arial", 36, QFont.Bold)
        self.setFont(font)

        # Default style
        self.setStyleSheet(
            "QLabel { color: white; background-color: navy; border-radius: 12px; }"
        )

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

        # Timer for blinking
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_blink)
        self.blink_state = True

    def set_state(self, state):
        """Set status text and style"""
        styles = {
            "RUNNING": ("RUNNING", "orange"),
            "WAITING": ("WAITING", "gray"),
            "STOP": ("STOP", "black"),
            "PASS": ("PASS", "green"),
            "FAIL": ("FAIL", "red"),
        }
        text, color = styles.get(state, ("UNKNOWN", "blue"))
        self.setText(text)
        self.setStyleSheet(
            f"""
            QLabel {{
                color: white;
                background-color: {color};
                border-radius: 12px;
            }}
        """
        )

        # Start flashing if FAIL
        if state == "RUNNING":
            self.blink_timer.start(500)  # Blink every 500ms
        else:
            self.blink_timer.stop()

    flag = True

    def _toggle_blink(self):
        """Toggle visibility for blinking effect"""
        if self.flag:
            self.setStyleSheet(
                f"""
                QLabel {{
                color: white;
                background-color: gold;
                border-radius: 12px;
            }}
        """
            )
        else:
            self.setStyleSheet(
                f"""
                QLabel {{
                color: white;
                background-color: orange;
                border-radius: 12px;
            }}
        """
            )
        self.flag = not self.flag


if __name__ == "__main__":
    app = QApplication(sys.argv)
    database_data = database_manager.load_database_data("database_data.yaml")
    b_config = test_process.load_basic_config("config_basic.yaml")
    window = BTTestApp(b_config, database_data)
    window.show()
    sys.exit(app.exec_())
