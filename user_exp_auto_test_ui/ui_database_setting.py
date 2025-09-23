import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFormLayout, QLabel,QGroupBox,
    QLineEdit, QDateEdit, QComboBox, QSpinBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import QDate


class DataBase_Data_setting(QWidget):
    def __init__(self, excel_path):
        super().__init__()
        self.setWindowTitle("Database Setting Form")
        self.resize(600, 500)
        group = QGroupBox()
        layout = QFormLayout()
        layout_form = QFormLayout()
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
        for _, row in df.iterrows():
            field = str(row["Name"])
            example = str(row["example"]) if not pd.isna(row["example"]) else ""
            required = str(row["Required fields"]).strip().lower() == "o"
            choices = str(row["possible selection"]) if not pd.isna(row["possible selection"]) else ""
            generate_ui = str(row["generate UI"]).strip().upper()

            if generate_ui == "X":
                continue  # skip this field

            label_text = field + (" *" if required else "")
            # Pick widget type
            if "date" in field.lower():
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
            elif choices and choices != "nan":
                widget = QComboBox()
                widget.addItems([c.strip() for c in choices.split(",")])
            elif example.isdigit():
                widget = QSpinBox()
                widget.setMaximum(999999)  # set some reasonable max
                widget.setValue(int(example))
            else:
                widget = QLineEdit()
                if example:
                    widget.setPlaceholderText(example)

            self.widgets[field] = widget
            layout.addRow(make_title(label_text), widget)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        layout.addRow(save_button)
        group.setLayout(layout)
        layout_form.addWidget(group)
        self.setLayout(layout_form)

    def save_data(self):
        """Collect all form values into a dict"""
        data = {}
        for field, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                data[field] = widget.text()
            elif isinstance(widget, QComboBox):
                data[field] = widget.currentText()
            elif isinstance(widget, QDateEdit):
                data[field] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QSpinBox):
                data[field] = widget.value()

        QMessageBox.information(self, "Saved Data", str(data))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataBase_Data_setting("database_data.xlsx")  # <--- your file path
    window.show()
    sys.exit(app.exec_())
