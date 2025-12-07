import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_manage_students import Ui_ManageStudents
from helper_files.shared_utilities import BaseLoginForm
from database_files.class_database_uitlities import DatabaseUtilities
from admin.class_admin_utilities import AdminUtilities, db

# Register courses page for a student
from student.submenus.class_register_courses import RegisterCoursesWidget
# Current schedule page (removing sections)
from student.submenus.class_current_schedule import CurrentScheduleWidget

# Add Grades dialog (the one we built earlier)
from admin.submenus.class_add_grades_dialog import AddGradesDialog


class ManageStudentsController:
    """
    Controller for Ui_ManageStudents.

    Behaviors:
    - Displays only active students.
    - Supports search by name, ID, email, and program.
    - Filters by program using comboBoxSelectProgram.
    - Updates student counter in labelTotalStudentsCount.

    Note:
    This controller handles only UI mapping and interactions. It uses admin_utils
    and db utilities for all data operations. No raw SQL is used here.
    """

    def __init__(self, ui: Ui_ManageStudents, admin_utils: AdminUtilities):
        self.ui = ui
        self.admin = admin_utils
        self.db = admin_utils.db
        self.students_data = []
        self.blf = BaseLoginForm()

        # Keep references for child windows to prevent garbage collection
        self.register_window = None
        self.current_schedule_window = None
        self.add_grades_window = None  # New: add grades dialog holder

        # Disable buttons initially
        self.ui.buttonAddStudent.setEnabled(False)
        self.ui.buttonRemoveSelected.setEnabled(False)

        # Optional: If the UI contains add grades button, disable first
        if hasattr(self.ui, "buttonAddGrades"):
            self.ui.buttonAddGrades.setEnabled(False)

        # Connect signals
        self.connect_ui_signals()

        # Initial load
        self.load_students()
        self.format_table()

    # ----------------------------------------------------
    # Connects all important UI signals
    # ----------------------------------------------------
    def connect_ui_signals(self):
        # Search text
        self.ui.lineEditSearch.textChanged.connect(self.search_and_filter)

        # Program filter
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.search_and_filter)

        # Refresh button
        self.ui.buttonRefresh.clicked.connect(self.handle_refresh)

        # Register courses for selected student
        self.ui.buttonAddStudent.clicked.connect(self.handle_add_student_courses)

        # Remove courses (opens CurrentScheduleWidget)
        self.ui.buttonRemoveSelected.clicked.connect(self.handle_remove_student_courses)

        # Add Grades button (safe check in case UI version does not have it)
        if hasattr(self.ui, "buttonAddGrades"):
            self.ui.buttonAddGrades.clicked.connect(self.handle_add_grades_for_student)

        # React when table selection changes
        self.ui.tableAllStudents.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )

        # First-time refresh animation and load
        self.handle_refresh()

    # ----------------------------------------------------
    # Load and filter students
    # ----------------------------------------------------
    def load_students(self):
        """
        Loads all users from db.list_users, then filters:
        - account_status == 'active'
        - state == 'student'

        Stores the result in self.students_data.
        """
        self.students_data.clear()
        self.ui.tableAllStudents.setRowCount(0)

        rows = self.db.list_users()

        active_rows = [
            row for row in rows
            if row[5] == "active" and row[4] == "student"
        ]

        for i, row in enumerate(active_rows, start=1):
            student = {
                "row_number": i,
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "program": row[3],  # may be None
                "state": row[4],
                "account_status": row[5],
            }
            self.students_data.append(student)

        self.fill_table(self.students_data)
        self.update_total_counter()

    def handle_refresh(self):
        """
        Displays a small animation using BaseLoginForm.animate_label_with_dots,
        then reloads students.
        """
        BaseLoginForm.animate_label_with_dots(
            self.ui.labelTotalStudentsCount,
            base_text="Refreshing",
            interval=400,
            duration=2000,
            on_finished=self.load_students
        )

    def format_table(self):
        """
        Formats table columns. Column count is already correct in UI:
        (#, ID, Name, Email, Program, State).
        """
        table = self.ui.tableAllStudents
        header = table.horizontalHeader()
        header.setStretchLastSection(True)

        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(60)

        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 220)
        table.setColumnWidth(3, 260)
        table.setColumnWidth(4, 110)
        table.setColumnWidth(5, 100)

    # ----------------------------------------------------
    # Fill table with given list of student dicts
    # ----------------------------------------------------
    def fill_table(self, students):
        table = self.ui.tableAllStudents
        table.setRowCount(len(students))

        for row_idx, student in enumerate(students):
            item_number = QTableWidgetItem(str(row_idx + 1))
            item_number.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 0, item_number)

            item_id = QTableWidgetItem(str(student["user_id"]))
            item_id.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 1, item_id)

            table.setItem(row_idx, 2, QTableWidgetItem(student["name"] or ""))
            table.setItem(row_idx, 3, QTableWidgetItem(student["email"] or ""))

            prog_text = student["program"] or ""
            table.setItem(row_idx, 4, QTableWidgetItem(prog_text))

            table.setItem(row_idx, 5, QTableWidgetItem(student["state"] or ""))

    # ----------------------------------------------------
    # Search and program filter (combined)
    # ----------------------------------------------------
    def search_and_filter(self):
        """
        Filters by:
        - search text: name, ID, email, program
        - program: selected in comboBoxSelectProgram
        """
        text = self.ui.lineEditSearch.text().strip().lower()
        program_filter = self.ui.comboBoxSelectProgram.currentText()

        program_map = {
            "Computer": "COMP",
            "Communication": "COMM",
            "Power": "PWM",
            "Biomedical": "BIO",
        }

        def match_program(s):
            if program_filter == "All Programs":
                return True
            code = program_map.get(program_filter)
            return (s["program"] or "") == code

        def match_text(s):
            if not text:
                return True
            return (
                text in (s["name"] or "").lower()
                or text in str(s["user_id"])
                or text in (s["email"] or "").lower()
                or text in (s["program"] or "").lower()
            )

        filtered = [s for s in self.students_data if match_program(s) and match_text(s)]
        self.fill_table(filtered)

    # ----------------------------------------------------
    # Enable or disable action buttons depending on selection
    # ----------------------------------------------------
    def on_selection_changed(self, *_):
        """
        Enables action buttons only when at least one row is selected.
        """
        selected_rows = self.ui.tableAllStudents.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.ui.buttonAddStudent.setEnabled(has_selection)
        self.ui.buttonRemoveSelected.setEnabled(has_selection)

        if hasattr(self.ui, "buttonAddGrades"):
            self.ui.buttonAddGrades.setEnabled(has_selection)

    # ----------------------------------------------------
    # Helper: get ID of single selected student (with validation)
    # ----------------------------------------------------
    def get_single_selected_student_id(self):
        table = self.ui.tableAllStudents
        selected = table.selectionModel().selectedRows()

        if not selected:
            QMessageBox.warning(None, "No Selection", "Please select a student.")
            return None

        if len(selected) > 1:
            QMessageBox.warning(None, "Multiple Selected", "Select only one student.")
            return None

        row = selected[0].row()
        item = table.item(row, 1)  # column 1 = ID

        if not item:
            QMessageBox.warning(None, "Error", "Could not read student ID.")
            return None

        try:
            return int(item.text())
        except ValueError:
            QMessageBox.warning(None, "Error", "Invalid student ID.")
            return None

    # ----------------------------------------------------
    # Register courses for student
    # ----------------------------------------------------
    def handle_add_student_courses(self):
        student_id = self.get_single_selected_student_id()
        if student_id is None:
            return

        self.register_window = RegisterCoursesWidget(student_id, semester=None)
        self.register_window.show()

    # ----------------------------------------------------
    # Remove sections for student (open current schedule)
    # ----------------------------------------------------
    def handle_remove_student_courses(self):
        student_id = self.get_single_selected_student_id()
        if student_id is None:
            return

        self.current_schedule_window = CurrentScheduleWidget(student_id)
        self.current_schedule_window.show()

    # ----------------------------------------------------
    # Add Grades for student
    # ----------------------------------------------------
    def handle_add_grades_for_student(self):
        """
        Opens AddGradesDialog for the selected student.
        The dialog itself filters available courses based on student registration.
        """
        student_id = self.get_single_selected_student_id()
        if student_id is None:
            return

        # Create the AddGradesDialog (admin_utils is already available)
        self.add_grades_window = AddGradesDialog(self.admin, self.db)
        self.add_grades_window.show()

    # ----------------------------------------------------
    # Update student counter
    # ----------------------------------------------------
    def update_total_counter(self):
        self.ui.labelTotalStudentsCount.setText(
            f"Total Students: {len(self.students_data)}"
        )


# Testing (standalone mode)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    admin_utils = AdminUtilities(db)

    window = QWidget()
    ui = Ui_ManageStudents()
    ui.setupUi(window)

    controller = ManageStudentsController(ui, admin_utils)

    window.show()
    sys.exit(app.exec())
