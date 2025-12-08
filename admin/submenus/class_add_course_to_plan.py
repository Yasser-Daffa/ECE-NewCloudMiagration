import os
import sys

from PyQt6.QtWidgets import QApplication, QDialog

# Add the main project directory to sys.path so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.admin_ui.submenus_ui.ui_add_course_to_plan_dialog import Ui_AddCourseDialog
from helper_files.shared_utilities import info, error


class AddCourseToPlanDialog(QDialog):
    """
    Dialog for adding a course to a study plan:
    - Select a course
    - Select a program (PWM/BIO/COMM/COMP)
    - Select a Level
    - Calls admin_add_course_to_plan
    """

    def __init__(self, admin_utils, parent=None):
        super().__init__(parent)

        self.ui = Ui_AddCourseDialog()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils
        self.db = admin_utils.db

        # Fill combo boxes on startup
        self.populate_courses_combo()
        self.populate_programs_combo()

        # Save button initially disabled until all fields are valid
        self.ui.buttonSave.setEnabled(False)

        # Connect buttons
        self.ui.buttonSave.clicked.connect(self.on_save_clicked)
        self.ui.buttonCancel.clicked.connect(self.reject)

        # Connect validation triggers
        self.ui.comboBoxSelectCourse.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.check_all_fields_filled)
        self.ui.spinBoxLevel.valueChanged.connect(self.check_all_fields_filled)

        # Initial validation call
        self.check_all_fields_filled()

    # ------------------------ COMBO BOX POPULATION ------------------------

    def populate_courses_combo(self):
        """Fill the course list from the courses table."""
        cb = self.ui.comboBoxSelectCourse
        cb.clear()
        cb.addItem("Select a course...", None)

        # ListCourses returns (code, name, credits)
        rows = self.admin_utils.db.ListCourses()

        # Add courses in readable format
        for code, name, credits in rows:
            cb.addItem(f"{code} - {name}", code)

        # Added comment: Now the combo box has each course's display name and code stored as its data.

    def populate_programs_combo(self):
        """Fill available programs using a static list."""
        cb = self.ui.comboBoxSelectProgram
        cb.clear()
        cb.addItem("Select program...", None)

        # List of supported programs and labels
        programs = [
            ("PWM",  "Power & Machines Engineering"),
            ("BIO",  "Biomedical Engineering"),
            ("COMM", "Communications Engineering"),
            ("COMP", "Computer Engineering"),
        ]

        for code, label in programs:
            cb.addItem(f"{code} - {label}", code)

        # Added comment: User sees label, program code is stored internally.

    # ------------------------ SAVE BUTTON ACTIVATION ------------------------

    def check_all_fields_filled(self):
        """Enable the Save button only when all required fields have valid selections."""
        course_ok = self.ui.comboBoxSelectCourse.currentIndex() > 0
        program_ok = self.ui.comboBoxSelectProgram.currentIndex() > 0
        level_ok = self.ui.spinBoxLevel.value() >= 1

        # Button becomes enabled only when all conditions are satisfied
        self.ui.buttonSave.setEnabled(course_ok and program_ok and level_ok)

    def on_save_clicked(self):
        """Called when Save is pressed. Validates and sends data to admin utilities."""
        course_code = self.ui.comboBoxSelectCourse.currentData()
        program = self.ui.comboBoxSelectProgram.currentData()
        level = self.ui.spinBoxLevel.value()

        # Added info: The admin layer handles duplicate checking and plan validation.

        try:
            msg = self.admin_utils.admin_add_course_to_plan(
                program=program,
                course_code=course_code,
                level=level,
            )
        except Exception as e:
            error(self, f"Error while adding course to plan:\n{e}")
            return

        # Show success message returned from DB layer
        info(self, msg)

        # Reset UI state after successful insert
        self.ui.comboBoxSelectCourse.setCurrentIndex(0)
        self.ui.spinBoxLevel.setValue(1)

        # Refresh button state
        self.check_all_fields_filled()

        # Do not close the window after saving
        return


# =============== MAIN FOR TESTING ===============

if __name__ == "__main__":
    app = QApplication(sys.argv)


    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    dlg = AddCourseToPlanDialog(admin_utils)

    dlg.show()
    sys.exit(app.exec())
