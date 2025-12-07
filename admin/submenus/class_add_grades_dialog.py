# admin/submenus/class_add_grades_dialog.py

import os, sys
# Ensure project root is available in the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QDialog, QApplication
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_add_grades import Ui_AddGradesDialog
from helper_files.shared_utilities import warning, info, error
from admin.class_admin_utilities import AdminUtilities
from database_files.class_database_uitlities import DatabaseUtilities


class AddGradesDialog(QDialog):
    """
    Dialog for adding or updating a student's grade.
    - Uses ONLY admin_utils + db utils.
    - Shows ONLY courses the student is currently registered in.
    - Disables grade selection until a course is chosen.
    - Semester year is provided by admin; semester name comes from registration data.
    """

    def __init__(self, admin_utils: AdminUtilities, db: DatabaseUtilities, parent=None):
        super().__init__(parent)

        self.ui = Ui_AddGradesDialog()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils
        self.db = db

        self.setWindowTitle("Add Grades")
        self.setModal(True)

        # Connect cancel/save buttons
        self.ui.buttonCancel.clicked.connect(self.reject)
        self.ui.buttonSave.clicked.connect(self.save_grade)


        # Load the list of active students
        self.load_students()

        # Course list updates when a student is selected
        self.ui.comboBoxStudentID.currentIndexChanged.connect(self.on_student_changed)


    # ---------------------------------------------------------
    def load_students(self):
        """
        Load all active students into the student dropdown.
        Only users with state='student' and status='active' should appear.
        """
        self.ui.comboBoxStudentID.clear()
        self.ui.comboBoxStudentID.addItem("Select student...", None)

        for row in self.db.list_users():
            # Expected row format: (uid, name, email, program, state, status, ...)
            if len(row) < 6:
                continue

            uid, name, email, program, state, status = row[:6]

            if state == "student" and status == "active":
                self.ui.comboBoxStudentID.addItem(f"{uid} — {name}", uid)

    # ---------------------------------------------------------
    def on_student_changed(self):
        """
        Load ONLY the courses that the selected student is registered in.
        If no student is selected, fields reset.
        """
        student_id = self.ui.comboBoxStudentID.currentData()

        self.ui.comboBoxSelectCourse.clear()
        self.ui.comboBoxSelectCourse.addItem("Select a course...", None)

        # Reset grade and save button
        self.ui.buttonSave.setEnabled(False)

        if student_id is None:
            return

        # Registrations: each row is expected to be (student_id, section_id, course_code, semester)
        regs = self.db.list_registrations(student_id)

        if not regs:
            warning(self, "This student has no registered courses.")
            return

        # Avoid duplicates if the student is registered in multiple sections of same course
        seen = set()
        for _, section_id, course_code, semester in regs:
            if course_code not in seen:
                self.ui.comboBoxSelectCourse.addItem(course_code, course_code)
                seen.add(course_code)

        # Save can be enabled after a course is selected
        self.ui.buttonSave.setEnabled(True)
        # Enable grade selection when courses are loaded



    # ---------------------------------------------------------
    def validate_inputs(self):
        """
        Validate selections:
        - Student selected
        - Course selected
        - Grade selected
        - Semester year present
        Returns tuple if valid, otherwise shows warnings.
        """
        student_id = self.ui.comboBoxStudentID.currentData()
        course_code = self.ui.comboBoxSelectCourse.currentData()
        grade = self.ui.comboBoxGrade.currentText().strip()
        year = self.ui.spinBoxSemesterYear.value()

        if student_id is None:
            warning(self, "Please select a student.")
            return None

        if course_code is None:
            warning(self, "Please select a course.")
            return None

        if grade == "":
            warning(self, "Please select a grade.")
            return None

        return int(student_id), course_code, grade, year

    # ---------------------------------------------------------
    def save_grade(self):
        """
        Save or update a student's grade:
        - Confirm registration exists
        - Determine semester name from registration
        - Insert/update transcript
        - Remove student registration after final grade is recorded
        """
        validated = self.validate_inputs()
        if validated is None:
            return

        student_id, course_code, grade, year = validated

        try:
            # List registration for that specific course
            regs = self.db.list_registrations(student_id, course_code)

            if not regs:
                warning(self, "This student is not registered in this course.")
                return

            reg = regs[0]
            if len(reg) < 4:
                raise ValueError(f"Invalid registration row: {reg}")

            _, section_id, reg_course_code, semester_name = reg

            # Safety: ensure the registration matches the course code
            if reg_course_code != course_code:
                raise ValueError("Registration mismatch.")

            # Example final semester format: "2025 First"
            final_semester = f"{year} {semester_name}"

            transcript = self.db.list_transcript(student_id)
            exists = any(row[0] == course_code for row in transcript)

            # Update if exists, otherwise insert
            if exists:
                self.db.update_transcript_grade(
                    student_id, course_code, final_semester, grade
                )
                info(self, f"Updated grade for {course_code}.")
            else:
                self.db.add_transcript(
                    student_id, course_code, final_semester, grade
                )
                info(self, f"Added grade for {course_code}.")

            # Attempt to remove registration entry after grade is recorded
            try:
                self.db.remove_student_registration(student_id, course_code)
            except Exception as e:
                print(f"[WARN] remove_student_registration failed: {e}")

        

        except Exception as e:
            error(self, f"An error occurred while saving grade:\n{e}")


# Standalone Test
if __name__ == "__main__":
    app = QApplication(sys.argv)

    from admin.class_admin_utilities import admin as admin_utils, db

    dlg = AddGradesDialog(admin_utils, db)
    dlg.show()

    sys.exit(app.exec())
