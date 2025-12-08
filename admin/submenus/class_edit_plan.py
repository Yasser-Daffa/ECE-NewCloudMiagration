import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
)

# Add main project folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.admin_ui.submenus_ui.ui_edit_course_to_plan_dialog import Ui_AddCourseDialog
from helper_files.shared_utilities import info, error


class EditCourseToPlanDialog(QDialog):
    """
    Dialog for editing a course inside a study plan:
    - Receives the old values (program, course_code, level) from the table.
    - Displays them in the UI.
    - On Save:
        Calls admin_update_course_to_plan (which performs an SQL UPDATE).
    """

    def __init__(self, admin_utils, old_program, old_course_code, old_level, parent=None):
        super().__init__(parent)

        self.ui = Ui_AddCourseDialog()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils
        self.db = admin_utils.db

        # Store old values (strip whitespace & normalize case)
        self.old_program = (old_program or "").strip().upper()
        self.old_course_code = (old_course_code or "").strip().upper()
        self.old_level = old_level

        # Populate combo boxes
        self.populate_courses_combo()
        self.populate_programs_combo()

        # Preselect the old values in the UI
        self.preselect_old_values()

        # Save button initially disabled
        self.ui.buttonSave.setEnabled(False)

        # Connect buttons
        self.ui.buttonSave.clicked.connect(self.on_save_clicked)
        self.ui.buttonCancel.clicked.connect(self.reject)

        # Validation triggers
        self.ui.comboBoxSelectCourse.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.spinBoxLevel.valueChanged.connect(self.check_all_fields_filled)

        self.check_all_fields_filled()

    # ------------------------ Populate combos ------------------------

    def populate_courses_combo(self):
        """Fill the course list from the courses table."""
        cb = self.ui.comboBoxSelectCourse
        cb.clear()
        cb.addItem("Select a course...", None)

        rows = self.admin_utils.db.ListCourses()  # (code, name, credits)
        for code, name, credits in rows:
            display = f"{code} - {name}"     # what the user sees
            cb.addItem(display, code.upper())  # stored data is the code

    def populate_programs_combo(self):
        """Fill the program list using a fixed list of programs."""
        cb = self.ui.comboBoxSelectProgram
        cb.clear()
        cb.addItem("Select program...", None)

        programs = [
            ("PWM",  "Power & Machines Engineering"),
            ("BIO",  "Biomedical Engineering"),
            ("COMM", "Communications Engineering"),
            ("COMP", "Computer Engineering"),
        ]

        for code, label in programs:
            cb.addItem(f"{code} - {label}", code.upper())

    def preselect_old_values(self):
        """
        Selects the old program, old course, and old level in the UI.
        Matching is based on comboBox itemData (not display text).
        """

        # 1) Course
        cb_course = self.ui.comboBoxSelectCourse
        for i in range(cb_course.count()):
            data = cb_course.itemData(i)
            if data is not None and str(data).upper() == self.old_course_code:
                cb_course.setCurrentIndex(i)
                break

        # 2) Program
        cb_prog = self.ui.comboBoxSelectProgram
        for i in range(cb_prog.count()):
            data = cb_prog.itemData(i)
            if data is not None and str(data).upper() == self.old_program:
                cb_prog.setCurrentIndex(i)
                break

        # 3) Level
        try:
            lvl = int(self.old_level)
        except (TypeError, ValueError):
            lvl = 1
        self.ui.spinBoxLevel.setValue(lvl)

    # ------------------------ Enable save button ------------------------

    def check_all_fields_filled(self):
        """
        Enables Save only if:
        - Course is selected
        - Program is selected
        - Level >= 1
        """
        course_ok = self.ui.comboBoxSelectCourse.currentIndex() > 0
        program_ok = self.ui.comboBoxSelectProgram.currentIndex() > 0
        level_ok = self.ui.spinBoxLevel.value() >= 1

        self.ui.buttonSave.setEnabled(course_ok and program_ok and level_ok)

    # ------------------------ Save button event ------------------------

    def on_save_clicked(self):
        """
        Reads new inputs and sends them to admin_update_course_to_plan.
        Old values are stored in self.old_program / self.old_course_code / self.old_level.
        """

        # New values from data (not display text)
        new_course_code = self.ui.comboBoxSelectCourse.currentData()
        new_program = self.ui.comboBoxSelectProgram.currentData()
        new_level = self.ui.spinBoxLevel.value()

        if not new_course_code or not new_program or new_level < 1:
            error(self, "Please fill all required fields.")
            return

        # Normalize
        new_course_code = str(new_course_code).strip().upper()
        new_program = str(new_program).strip().upper()

        try:
            old_level_int = int(self.old_level)
        except (TypeError, ValueError):
            old_level_int = new_level

        # Perform UPDATE via admin method
        try:
            msg = self.admin_utils.admin_update_course_to_plan(
                old_program=self.old_program,
                old_course_code=self.old_course_code,
                old_level=old_level_int,
                new_program=new_program,
                new_course_code=new_course_code,
                new_level=new_level,
            )
        except Exception as e:
            error(self, f"Error while updating course in plan:\n{e}")
            return

        # If DB returned a failure message
        if msg.startswith("✗") or "already" in msg.lower():
            error(self, msg)
            return

        # Success
        info(self, msg)

        # Update stored old values (for future edits without closing dialog)
        self.old_program = new_program
        self.old_course_code = new_course_code
        self.old_level = new_level

        # Close dialog after successful update
        self.accept()


# =============== Standalone Test ===============
if __name__ == "__main__":
    app = QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)
    
    dlg = EditCourseToPlanDialog(admin_utils, "COMP", "CPE101", 1)
    dlg.show()

    sys.exit(app.exec())
