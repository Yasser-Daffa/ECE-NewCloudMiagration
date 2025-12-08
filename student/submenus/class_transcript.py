import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt

# Ensure access to the project root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Transcript UI (Qt Designer)
from app_ui.student_ui.submenus_ui.ui_transcript import Ui_Transcript

# Student utilities + database reference

class TranscriptWidget(QWidget):
    """
    Transcript Display Widget:
    - Retrieves all student transcript entries from the transcripts table.
    - Fills tableCourses with:
        #, COURSE CODE, COURSE NAME, CREDIT, GRADE, SEMESTER
    - Updates:
        - GPA
        - Completed Credits
        - Current Credits
      using simple logic.
    """

    def __init__(self, student_utils, admin_utils=None, parent=None):
        super().__init__(parent)

        self.ui = Ui_Transcript()
        self.ui.setupUi(self)

        self.student_utils = student_utils
        self.admin_utils = admin_utils
        self.db = student_utils.db
        self.student_id = student_utils.student_id

        # This widget only displays transcript history.


        # Prepare the main transcript table
        self.setup_table()

        # Refresh button
        self.ui.buttonRefresh.clicked.connect(self.load_transcript)

        # Load student info + transcript
        self.load_student_info()
        self.load_transcript()

    # ==================== Table Setup ====================

    def setup_table(self):
        """Configure the transcript table appearance and columns."""
        table = self.ui.tableCourses
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.SingleSelection)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)

        table.setColumnCount(6)
        headers = ["#", "COURSE CODE", "COURSE NAME", "CREDIT", "GRADE", "SEMESTER"]
        table.setHorizontalHeaderLabels(headers)

        # Basic column sizing
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 140)
        table.setColumnWidth(2, 320)
        table.setColumnWidth(3, 80)
        table.setColumnWidth(4, 80)
        table.setColumnWidth(5, 140)

    # ==================== Student Header Info ====================

    def load_student_info(self):
        """
        Displays the student's program in labelMajor only.
        No name, no ID, no department details.
        """
        try:
            user = self.student_utils.db.get_user_by_id(self.student_id)
            # (user_id, name, email, program, state, account_status)
        except Exception as e:
            print(f"[ERROR] load_student_info: {e}")
            user = None

        program = user[3] if user else "N/A"

        # Display program only
        if hasattr(self.ui, "labelMajor"):
            self.ui.labelMajor.setText(f"{program}")

        # Department label intentionally left blank
        if hasattr(self.ui, "labelDepartment"):
            self.ui.labelDepartment.setText("")

    # ==================== Transcript Loading ====================

    def load_transcript(self):
        """
        Loads student transcript entries from DB, fills the table,
        and calculates:
        - Completed Credits
        - Current Registered Credits
        - GPA (basic version)
        """
        table = self.ui.tableCourses
        table.setRowCount(0)

        # Fetch all transcript entries (course_code, semester, grade)
        try:
            rows = self.student_utils.db.list_transcript(self.student_id)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load transcript:\n{e}")
            return

        # Load all courses once to get names + credits
        # (code, name, credits)
        courses_info = self.student_utils.db.ListCourses()
        course_map = {c[0]: (c[1], c[2]) for c in courses_info}

        total_completed_credits = 0
        total_points = 0.0
        total_credits_for_gpa = 0

        # Basic grade → point mapping (modify if needed)
        grade_points = {
            "A+": 5.0,
            "A": 4.75,
            "B+": 4.5,
            "B": 4.0,
            "C+": 3.5,
            "C": 3.0,
            "D+": 2.5,
            "D": 2.0,
            "F": 1.0,
        }

        table.setRowCount(len(rows))

        for i, (course_code, semester, grade) in enumerate(rows):
            name, credits = course_map.get(course_code, (course_code, 0))
            credits = credits or 0

            # ----- Column # -----
            item_idx = QTableWidgetItem(str(i + 1))
            item_idx.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 0, item_idx)

            # COURSE CODE
            item_code = QTableWidgetItem(course_code)
            item_code.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 1, item_code)

            # COURSE NAME
            item_name = QTableWidgetItem(str(name))
            item_name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 2, item_name)

            # CREDIT
            item_credits = QTableWidgetItem(str(credits))
            item_credits.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 3, item_credits)

            # GRADE
            grade_text = grade if grade is not None else ""
            item_grade = QTableWidgetItem(grade_text)
            item_grade.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 4, item_grade)

            # SEMESTER
            item_semester = QTableWidgetItem(str(semester))
            item_semester.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(i, 5, item_semester)

            # Completed credits count (if a grade exists)
            if grade is not None and grade != "":
                total_completed_credits += credits

                # GPA contribution (if grade is valid)
                gp = grade_points.get(str(grade).upper())
                if gp is not None and credits > 0:
                    total_points += gp * credits
                    total_credits_for_gpa += credits

        # ================= Statistics Update =================

        # Completed Credits
        if hasattr(self.ui, "labelCompletedCreditsCount"):
            self.ui.labelCompletedCreditsCount.setText(str(total_completed_credits))

        # Current Credits → total credits for currently registered courses
        current_credits = 0
        try:
            current_regs = self.student_utils.get_registered_courses_full()
            for reg in current_regs:
                current_credits += reg.get("credit", 0)
        except Exception as e:
            print(f"[WARN] Failed to compute current credits: {e}")

        if hasattr(self.ui, "labelCurrentCreditsCount"):
            self.ui.labelCurrentCreditsCount.setText(str(current_credits))

        # GPA
        if total_credits_for_gpa > 0:
            gpa = total_points / total_credits_for_gpa
            gpa_text = f"{gpa:.2f}"
        else:
            gpa_text = "N/A"

        if hasattr(self.ui, "labelGPACount"):
            self.ui.labelGPACount.setText(gpa_text)

        # Semester GPA & credits (optional, simplified as N/A)
        if hasattr(self.ui, "labelSemesterGPA"):
            self.ui.labelSemesterGPA.setText("Semester GPA: N/A")

        if hasattr(self.ui, "labelSemesterCreditsCount"):
            self.ui.labelSemesterCreditsCount.setText("Credits: N/A")


# ===== Stand-alone test runner =====
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Change this ID to a real student existing in database
    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from student.class_student_utilities import StudentUtilities
    from admin.class_admin_utilities import AdminUtilities

    # Create pooled DB
    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    # Create utilities
    student_utils = StudentUtilities(db, 2500001)
    admin_utils = AdminUtilities(db)

    w = TranscriptWidget(student_utils, admin_utils)
    w.show()


    sys.exit(app.exec())