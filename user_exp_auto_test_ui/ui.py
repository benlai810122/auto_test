from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QCheckBox,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
import sys
import test_process
from test_process import Basic_Config
from utils import log  as logger




class BTTestApp(QWidget):
    b_config:Basic_Config = None
    def __init__(self, b_config:Basic_Config):
        super().__init__()
        self.setWindowTitle("User Experience Auto Test")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
        self.b_config = b_config

    def init_ui(self):
        layout = QVBoxLayout()

        # --- device check ---
        check_layout = QHBoxLayout()
        self.ardu_check_button = QPushButton("Arduino board Check")
        self.ardu_check_button.clicked.connect(self.serial_port_check)
        check_layout.addWidget(self.ardu_check_button)

        # --- Device Selection ---
        device_group = QGroupBox("Device Selection")
        device_layout = QFormLayout()

        self.headset_combo = QComboBox()
        self.headset_combo.addItems(["Dell3024","Dell5024","Logitech H340","WH-1000XM4","None"])

        self.mouse_combo = QComboBox()
        self.mouse_combo.addItems(["Logitech M331", "Razer Basilisk", "HP X500","other","None"])

        device_layout.addRow("Headset:", self.headset_combo)
        device_layout.addRow("Mouse:", self.mouse_combo)
        device_group.setLayout(device_layout)

        # --- Test Case Selection ---
        test_case_group = QGroupBox("Test Case Selection")
        test_layout = QVBoxLayout()

        self.mouse_check = QCheckBox("Mouse Function Test")
        self.input_check = QCheckBox("Headset Input Test")
        self.output_check = QCheckBox("Headset Output Test")

        self.mouse_check.setChecked(True)
        self.input_check.setChecked(True)
        self.output_check.setChecked(True)

        test_layout.addWidget(self.mouse_check)
        test_layout.addWidget(self.input_check)
        test_layout.addWidget(self.output_check)
        test_case_group.setLayout(test_layout)

        # --- Log Output ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Test log will appear here...")

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.run_test)
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.quit_button)

        # --- Combine All Layouts ---
        layout.addLayout(check_layout)
        layout.addWidget(device_group)
        layout.addWidget(test_case_group)
        layout.addWidget(QLabel("Test Progress:"))
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    # Run test logic and log output to UI and log file
    def log_to_ui(self,msg):
        self.log_output.append(msg)
        logger.info(msg)

    def serial_port_check(self):
        self.log_output.clear()  # Clear previous logs
        test_process.get_arduino_port(port=self.b_config.target_port_desc, log_callback=self.log_to_ui)

    def run_test(self):
        test_process.run_test(b_config=self.b_config,log_callback= self.log_to_ui)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    b_config = test_process.load_basic_config("config_basic.yaml")
    window = BTTestApp(b_config=b_config)
    window.show()
    sys.exit(app.exec_())
