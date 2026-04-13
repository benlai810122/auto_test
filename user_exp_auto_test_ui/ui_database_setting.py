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
from utils import log as logger


class DataBase_Data_setting(QWidget):
    setting_changed = pyqtSignal(object)
    def __init__(self, excel_path, database_data: Database_data):
        super().__init__()
        self.database_data = database_data
        self._closing_from_save = False
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
            value = getattr(database_data, code, "")
            if type(self.widgets[code]) == QComboBox:
                self.widgets[code].setEditText(str(value))
            elif type(self.widgets[code]) == QSpinBox:
                try:
                    self.widgets[code].setValue(int(value))
                except (TypeError, ValueError):
                    self.widgets[code].setValue(0)
            else:
                self.widgets[code].setText(str(value))

        # auto filled the specific fold:
        driver_info = dbm.get_driver_versions()
        wrt_info = dbm.get_wrt_version_and_preset()
        self._set_widget_value('serial_num', dbm.get_serial_number(), disable=True)
        self._set_widget_value('os_version', dbm.get_os_version(), disable=True)
        self._set_widget_value('platform_brand', dbm.get_platform_brand(), disable=True)
        self._set_widget_value('platform', dbm.get_platform_name(), disable=True)
        self._set_widget_value('platform_bios', dbm.get_bios_version(), disable=True)
        self._set_widget_value('cpu', dbm.get_cpu_name(), disable=True)

        if driver_info.get(dbm.DRIVER_WLAN):
            self._set_widget_value('wlan', driver_info.get(dbm.DRIVER_WLAN), disable=True)
        if driver_info.get(dbm.DRIVER_BT):
            self._set_widget_value('bt_driver', driver_info.get(dbm.DRIVER_BT), disable=True)
        elif driver_info.get(dbm.DRIVER_BT_DUAL):
            self._set_widget_value('bt_driver', driver_info.get(dbm.DRIVER_BT_DUAL), disable=True)
        if driver_info.get(dbm.DRIVER_WIFI):
            self._set_widget_value('wifi_driver', driver_info.get(dbm.DRIVER_WIFI), disable=True)
        if driver_info.get(dbm.DRIVER_ISST):
            self._set_widget_value('audio_driver', driver_info.get(dbm.DRIVER_ISST), disable=True)
        if wrt_info and wrt_info.get('ver'):
            self._set_widget_value('wrt_version', wrt_info.get('ver'), disable=True)
        if wrt_info and wrt_info.get('preset'):
            self._set_widget_value('wrt_preset', wrt_info.get('preset'), disable=True)

        self._set_widget_value('msft_teams_version', dbm.get_teams_version(), disable=True)

        self._set_widget_value('wifi_name', dbm.get_connected_wifi_name(), disable=True)
        self._set_widget_value('wifi_band', dbm.get_connected_wifi_band(), disable=True)

    def _set_widget_value(self, code: str, value, disable: bool = False):
        widget = self.widgets.get(code)
        if widget is None:
            logger.warning(f"UI field missing for code '{code}'")
            return

        safe_value = "" if value is None else str(value)
        if isinstance(widget, QComboBox):
            widget.setEditText(safe_value)
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(value))
            except (TypeError, ValueError):
                widget.setValue(0)
        else:
            widget.setText(safe_value)

        if disable:
            widget.setDisabled(True)
    
    def save_data(self):
        #database_data update
        self._update_database_data_from_widgets()
        # check the required item have value
        if dbm.database_data_checking(self.database_data, self.required_datas):
            self.setting_changed.emit(self.database_data)
            self._closing_from_save = True
            self.close()
        else: 
            QMessageBox.warning(self,"Warning!","Please fill all required field!")

    def _update_database_data_from_widgets(self):
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
    
    def closeEvent(self, event):
        if self._closing_from_save:
            event.accept()
            return

        self._update_database_data_from_widgets()
        if dbm.database_data_checking(self.database_data, self.required_datas):
            self.setting_changed.emit(self.database_data)
            event.accept()
        else:
            QMessageBox.warning(self, "Warning!", "Please fill all required field!")
            event.ignore()

    
   

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = dbm.load_database_data("database_data.yaml")
    window = DataBase_Data_setting("database_data.xlsx", data)  # <--- your file path
    window.show()
    sys.exit(app.exec_())
