import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
)

# Add the full project path so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Add Section dialog UI (from Qt Designer)
from app_ui.admin_ui.submenus_ui.ui_add_sections_dialog import Ui_AddSectionDialog

# Shared tools class (shake effect, field highlighting, validation)
from helper_files.shared_utilities import BaseLoginForm

# Pre-built admin instance
from admin.class_admin_utilities import admin


class AddSectionDialog(QDialog, BaseLoginForm):
    """
    Dialog responsible for:
    - Reading fields from the Add Section UI
    - Validating required inputs
    - Calling add_section in the database through admin_utils
    """

    def __init__(self, admin_utils, parent=None):
        QDialog.__init__(self, parent)
        BaseLoginForm.__init__(self, parent)

        self.ui = Ui_AddSectionDialog()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils     # this is the ready-made admin instance

        # Prepare course combo box using data from the courses table
        self.populate_courses_combo()

        # Initially disable the Add button
        self.ui.buttonAdd.setEnabled(False)

        # Connect buttons
        self.ui.buttonAdd.clicked.connect(self.on_add_clicked)
        self.ui.buttonCancel.clicked.connect(self.reject)

        # Validation for important text fields (shake + border highlight if needed)
        self.attach_non_empty_validator(self.ui.lineEditBuilding, "Building")
        self.attach_non_empty_validator(self.ui.lineEditRoom, "Room")

        # Check button state whenever any field changes
        self.ui.comboBoxSelectCourse.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.comboBoxSelectTerm.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.comboBoxSelectStatus.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.lineEditBuilding.textChanged.connect(self.check_all_fields_filled)
        self.ui.lineEditRoom.textChanged.connect(self.check_all_fields_filled)
        self.ui.spinBoxCapacity.valueChanged.connect(self.check_all_fields_filled)

        # Day buttons also affect validation state
        self.ui.pushButtonDaySun.toggled.connect(self.check_all_fields_filled)
        self.ui.pushButtonDayMon.toggled.connect(self.check_all_fields_filled)
        self.ui.pushButtonDayTue.toggled.connect(self.check_all_fields_filled)
        self.ui.pushButtonDayWed.toggled.connect(self.check_all_fields_filled)
        self.ui.pushButtonDayThu.toggled.connect(self.check_all_fields_filled)

        # Initial validation
        self.check_all_fields_filled()

    # ------------------------ Populate course combo ------------------------

    def populate_courses_combo(self):
        """
        Retrieves courses using ListCourses and fills comboBoxSelectCourse.
        """
        self.ui.comboBoxSelectCourse.clear()
        self.ui.comboBoxSelectCourse.addItem("Select a course.", None)

        # Using database instance inside admin utils
        rows = self.admin_utils.db.ListCourses()  # [(code, name, credits), ...]

        for code, name, credits in rows:
            display = f"{code} - {name}"
            self.ui.comboBoxSelectCourse.addItem(display, code)

    # ------------------------ Enable/Disable Add button ------------------------

    def check_all_fields_filled(self):
        """
        Determines whether the Add button should be enabled based on:
        - Course selected
        - Term selected
        - Status selected
        - Building and Room text inputs
        - Capacity > 0
        - At least one day selected
        """

        course_ok = self.ui.comboBoxSelectCourse.currentIndex() > 0
        term_ok = self.ui.comboBoxSelectTerm.currentIndex() > 0
        status_ok = self.ui.comboBoxSelectStatus.currentIndex() > 0

        building = self.ui.lineEditBuilding.text().strip()
        room = self.ui.lineEditRoom.text().strip()
        capacity_ok = self.ui.spinBoxCapacity.value() > 0

        days_ok = any([
            self.ui.pushButtonDaySun.isChecked(),
            self.ui.pushButtonDayMon.isChecked(),
            self.ui.pushButtonDayTue.isChecked(),
            self.ui.pushButtonDayWed.isChecked(),
            self.ui.pushButtonDayThu.isChecked(),
        ])

        if course_ok and term_ok and status_ok and building and room and capacity_ok and days_ok:
            self.ui.buttonAdd.setEnabled(True)
        else:
            self.ui.buttonAdd.setEnabled(False)

    # ------------------------ Message boxes with black text ------------------------

    def show_error(self, message: str):
        """Display a styled error message box."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("Error")
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(
            """
            QMessageBox {
                background-color: white;
                color: black;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 12pt;
            }
            QMessageBox QPushButton {
                color: black;
                padding: 6px 14px;
            }
            """
        )
        box.exec()

    def show_info(self, message: str):
        """Display a styled success/info message box."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Success")
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(
            """
            QMessageBox {
                background-color: white;
                color: black;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 12pt;
            }
            QMessageBox QPushButton {
                color: black;
                padding: 6px 14px;
            }
            """
        )
        box.exec()

    # ------------------------ Helper: Get selected days ------------------------

    def get_selected_days(self) -> str:
        """
        Returns selected days as a string such as: 'SUN,MON,WED'
        Useful for storing in database and for schedule conflict checks.
        """
        days = []
        buttons = [
            self.ui.pushButtonDaySun,
            self.ui.pushButtonDayMon,
            self.ui.pushButtonDayTue,
            self.ui.pushButtonDayWed,
            self.ui.pushButtonDayThu,
        ]
        for btn in buttons:
            if btn.isChecked():
                days.append(btn.text().strip())

        return ",".join(days)

    # ------------------------ Add button event handler ------------------------

    def on_add_clicked(self):
        """
        Reads all fields and calls db.add_section through admin_utils.db.

        Note: check_all_fields_filled ensures all required fields are valid.
        """

        # ---- Course ----
        course_code = self.ui.comboBoxSelectCourse.currentData()

        # ---- Term (semester) ----
        semester = self.ui.comboBoxSelectTerm.currentText().strip()

        # ---- State/status ----
        state = self.ui.comboBoxSelectStatus.currentText().strip().lower()

        # ---- Building and Room ----
        building = self.ui.lineEditBuilding.text().strip().upper()
        room = self.ui.lineEditRoom.text().strip().upper()
        full_room = f"{building} {room}".strip()

        # ---- Capacity ----
        capacity = self.ui.spinBoxCapacity.value()

        # ---- Days ----
        days = self.get_selected_days()

        # ---- Time ----
        start_qtime = self.ui.timeEditFrom.time()
        end_qtime = self.ui.timeEditTo.time()

        time_start = start_qtime.toString("HH:mm")
        time_end = end_qtime.toString("HH:mm")

        # Important validation: end time must be after start time
        if end_qtime <= start_qtime:
            self.show_error("End time must be after start time.")
            return

        # ---- Instructor (optional) ----
        doctor_id = None
        if self.ui.comboBoxSelectInstructor.currentIndex() > 0:
            data = self.ui.comboBoxSelectInstructor.currentData()
            try:
                doctor_id = int(data) if data is not None else None
            except (TypeError, ValueError):
                doctor_id = None

        # ===== Call database add_section =====
        try:
            msg = self.admin_utils.db.add_section(
                course_code=course_code,
                doctor_id=doctor_id,
                days=days,
                time_start=time_start,
                time_end=time_end,
                room=full_room,
                capacity=capacity,
                semester=semester,
                state=state,
            )
        except Exception as e:
            self.show_error(f"Error while adding section:\n{e}")
            return

        self.show_info(msg)


# =============================== MAIN (Direct Run) ===============================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = AddSectionDialog(admin)
    dialog.show()

    sys.exit(app.exec())
