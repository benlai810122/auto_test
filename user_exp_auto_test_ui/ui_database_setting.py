import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QLabel,
    QGroupBox,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QMessageBox,
    QScrollArea,
)
from PyQt5.QtCore import QDate
from database_manager import Database_data
import database_manager as dbm
from PyQt5.QtCore import pyqtSignal
import requests


class DataBase_Data_setting(QWidget):
    setting_changed = pyqtSignal(object)
    def __init__(self, excel_path, database_data: Database_data):
        super().__init__()
        self.database_data = database_data
        self.init_ui(excel_path)
        self.ui_renew(self.database_data)

    def init_ui(self, excel_path):
        self.setWindowTitle("Database Setting Form")
        self.resize(600, 500)
        group = QGroupBox()
        layout = QFormLayout()
        layout_form = QFormLayout()

        # Scroll area wrapper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # Container widget inside scroll
        container = QWidget()
        self.form_layout = QFormLayout(container)

        # Load Excel
        df = pd.read_excel(excel_path, sheet_name=0)
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
          
            """
        )

        def make_title(text):
            label = QLabel(text)
            label.setStyleSheet("font-size: 16px; font-weight: bold;")
            return label

        # Store widgets
        self.widgets = {}
        self.codes = []
        self.required_datas = []
        for _, row in df.iterrows():
            field = str(row["Name"])
            code = str(row["DB_CODE"])
            example = str(row["Example"]) if not pd.isna(row["Example"]) else ""
            required = str(row["Required Fields"]).strip().lower() == "o"
            choices = (
                str(row["Possible Selection"])
                if not pd.isna(row["Possible Selection"])
                else ""
            )
            generate_ui = str(row["Generate UI"]).strip().upper()

            if generate_ui == "X":
                continue  # skip this field

            if required:
                label_text = field + " *"
                self.required_datas.append(code) 
            else:
                label_text = field  

            # Pick widget type
            if choices and choices != "nan":
                widget = QComboBox()
                widget.addItems([c.strip() for c in choices.split(",")])
                widget.setEditable(True)
            elif example.isdigit():
                widget = QSpinBox()
                widget.setMaximum(999999)  # set some reasonable max
                widget.setValue(int(example))
            else:
                widget = QLineEdit()
                if example:
                    widget.setPlaceholderText(example)

            self.widgets[code] = widget
            self.codes.append(code)
            layout.addRow(make_title(label_text), widget)

        print(self.widgets)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        layout.addRow(save_button)
        group.setLayout(layout)
        self.form_layout.addWidget(group)

        # Put form inside scroll
        scroll.setWidget(container)

        layout_form.addWidget(scroll)
        self.setLayout(layout_form)

    def ui_renew(self, database_data: Database_data):
        # showing the UI status according to the last time status
        for code in self.codes:
            if type(self.widgets[code]) == QComboBox:
                self.widgets[code].setEditText(getattr(database_data, code))
            elif type(self.widgets[code]) == QSpinBox:
                value = int(getattr(database_data, code))
                self.widgets[code].setValue(value)
            else:
                self.widgets[code].setText(getattr(database_data, code))

        # auto filled the specific fold:
        driver_info = dbm.get_driver_versions()
        self.widgets['serial_num'].setText(dbm.get_serial_number())
        self.widgets['serial_num'].setDisabled(True)
        self.widgets['os_version'].setText(dbm.get_os_version())
        self.widgets['os_version'].setDisabled(True)
        self.widgets['platform_brand'].setText(dbm.get_platform_brand())
        self.widgets['platform_brand'].setDisabled(True)
        self.widgets['platform'].setText(dbm.get_platform_name())
        self.widgets['platform'].setDisabled(True)
        self.widgets['platform_bios'].setText(dbm.get_bios_version())
        self.widgets['platform_bios'].setDisabled(True)
        self.widgets['cpu'].setText(dbm.get_cpu_name())
        self.widgets['cpu'].setDisabled(True)

        if driver_info.get(dbm.DRIVER_WLAN):
            self.widgets['wlan'].setText(driver_info.get(dbm.DRIVER_WLAN))
            self.widgets['wlan'].setDisabled(True) 
        if driver_info.get(dbm.DRIVER_BT):
            self.widgets['bt_driver'].setText(driver_info.get(dbm.DRIVER_BT))
            self.widgets['bt_driver'].setDisabled(True)
        elif driver_info.get(dbm.DRIVER_BT_DUAL):
            self.widgets['bt_driver'].setText(driver_info.get(dbm.DRIVER_BT_DUAL))
            self.widgets['bt_driver'].setDisabled(True) 
        if driver_info.get(dbm.DRIVER_WIFI):
            self.widgets['wifi_driver'].setText(driver_info.get(dbm.DRIVER_WIFI))
            self.widgets['wifi_driver'].setDisabled(True)
        if driver_info.get(dbm.DRIVER_ISST):
            self.widgets['audio_driver'].setText(driver_info.get(dbm.DRIVER_ISST))
            self.widgets['audio_driver'].setDisabled(True)

        self.widgets['msft_teams_version'].setText(dbm.get_teams_version())
        self.widgets['msft_teams_version'].setDisabled(True)

        self.widgets['wifi_name'].setText(dbm.get_connected_wifi_name())
        self.widgets['wifi_name'].setDisabled(True)
        self.widgets['wifi_band'].setText(dbm.get_connected_wifi_band())
        self.widgets['wifi_band'].setDisabled(True)
    
    def save_data(self):
        #database_data update
        for code in self.codes:
            if type(self.widgets[code]) == QComboBox:
                value = self.widgets[code].currentText()
                setattr(self.database_data, code, value)
            elif type(self.widgets[code]) == QSpinBox:
                value = self.widgets[code].value()
                setattr(self.database_data, code, value)
            else:
                value = self.widgets[code].text()
                setattr(self.database_data, code, value)
        # check the required item have value
        if dbm.database_data_checking(self.database_data, self.required_datas):
            self.setting_changed.emit(self.database_data)
            self.close()
        else: 
            QMessageBox.warning(self,"Warning!","Please fill all required field!")
    
    def closeEvent(self, event):
        self.save_data()
        event.accept()  # Accept the close event

    
   

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = dbm.load_database_data("database_data.yaml")
    window = DataBase_Data_setting("database_data.xlsx", data)  # <--- your file path
    window.show()
    sys.exit(app.exec_())
