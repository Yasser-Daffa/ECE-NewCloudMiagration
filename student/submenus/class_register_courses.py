import sys, os
from PyQt6.QtWidgets import QApplication, QWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.student_ui.submenus_ui.ui_register_courses import Ui_RegisterCourses
from student.submenus.class_view_sections import ViewSectionsWidget
from helper_files.shared_utilities import show_msg
from student.class_student_utilities import StudentUtilities, db


class RegisterCoursesWidget(QWidget):
    """
    Register courses widget:
    - Supports multi-selection
    - Still preserves prerequisite rules:
        * ALL selected courses must be eligible (can_register=True)
    - Opens a modal dialog showing sections for ALL selected courses
    """

    def __init__(self, student_id: int, semester: str, parent=None):
        super().__init__(parent)

        # Load UI
        self.ui = Ui_RegisterCourses()
        self.ui.setupUi(self)

        # Utilities
        self.student_utils = StudentUtilities(db, student_id)
        self.semester = semester
        self.sections_windows = []    # old design, not used but kept for compatibility
        self.all_courses = []         # full list of available courses

        # -------------------------------
        # TABLE CONFIGURATION
        # -------------------------------
        table = self.ui.tableAllCourses

        # Select entire rows
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)

        # ENABLE multi-selection instead of single-selection
        table.setSelectionMode(table.SelectionMode.MultiSelection)

        # Prevent editing table cells
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)

        # When selected rows change → recheck prerequisites
        table.itemSelectionChanged.connect(self.on_table_selection_changed)

        # -------------------------------
        # BUTTON SIGNALS
        # -------------------------------
        self.ui.buttonRefresh.clicked.connect(self.load_courses)
        self.ui.lineEditSearch.textChanged.connect(self.apply_search_filter)

        # View Sections button stays disabled until valid selection
        self.ui.buttonViewSections.setEnabled(False)
        self.ui.buttonViewSections.clicked.connect(self.handle_view_sections)

        # Load initial table
        self.load_courses()
        self.format_table()

    # ============================
    # LOAD COURSES FROM DATABASE
    # ============================
    def load_courses(self):
        """
        Fetch all available courses for this student for this semester.
        """
        try:
            courses = self.student_utils.get_available_courses(self.semester)
        except Exception as e:
            show_msg(self, "Error", f"Failed to load courses:\n{e}")
            courses = []

        self.all_courses = courses
        self.fill_table(courses)

    # ============================
    # FILL TABLE WITH COURSES
    # ============================
    def fill_table(self, rows):
        """
        Populate the table widget with course data.
        """
        table = self.ui.tableAllCourses
        table.setRowCount(len(rows))

        for i, course in enumerate(rows):
            code = course["course_code"]
            name = course["course_name"]
            credits = course["credits"]
            can_register = course["can_register"]
            prereqs = ", ".join(course.get("prereqs", [])) or "None"
            level = course.get("level", "-")

            # Column: Row #
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.item(i, 0).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            # Column: Course Code
            code_item = QTableWidgetItem(code)
            code_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 1, code_item)

            # Column: Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 2, name_item)

            # Column: Credits
            credits_item = QTableWidgetItem(str(credits))
            credits_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 3, credits_item)

            # Column: Level
            level_item = QTableWidgetItem(level)
            level_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 4, level_item)

            # Column: Prerequisites
            prereq_item = QTableWidgetItem(prereqs)
            prereq_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 5, prereq_item)

            # Tooltip for clarity
            for col in range(6):
                item = table.item(i, col)
                if item:
                    item.setToolTip(f"Prerequisites: {prereqs}")

    # ============================
    # SEARCH FILTER
    # ============================
    def apply_search_filter(self):
        """
        Filter the table by course code or course name.
        """
        text = self.ui.lineEditSearch.text().strip().lower()
        if not text:
            self.fill_table(self.all_courses)
            return

        filtered = [
            c for c in self.all_courses
            if text in c["course_code"].lower() or text in c["course_name"].lower()
        ]

        self.fill_table(filtered)

    # ============================
    # TABLE FORMAT (HEADER, WIDTHS)
    # ============================
    def format_table(self):
        """
        Setup and format the table columns and headers.
        """
        table = self.ui.tableAllCourses

        headers = ["#", "Course Code", "Name", "Credits", "Level", "Prerequisites"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # Configure selection again just to be safe
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        table.verticalHeader().setDefaultSectionSize(60)

        # Column widths
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 300)
        table.setColumnWidth(3, 80)
        table.setColumnWidth(4, 80)
        table.setColumnWidth(5, 200)

        # Allow resizing + sorting
        table.setSortingEnabled(True)
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

    # ============================
    # HANDLE SELECTION CHANGES
    # ============================
    def on_table_selection_changed(self):
        """
        Enable or disable the View Sections button based on:
        - whether rows are selected
        - ALL selected courses must be eligible (prereqs met)
        - global registration lock (if closed, button is always disabled)
        """
        table = self.ui.tableAllCourses
        selected_rows = table.selectionModel().selectedRows()

        # Global registration lock: if closed, keep button disabled regardless of selection
        try:
            if not self.student_utils.db.is_registration_open():
                self.ui.buttonViewSections.setEnabled(False)
                self.ui.buttonViewSections.setToolTip(
                    "Course registration period is currently closed."
                )
                return
            else:
                # Clear tooltip when registration is open
                self.ui.buttonViewSections.setToolTip(
                    "View available sections for the selected courses."
                )
        except Exception as e:
            # Do not crash the UI if any error happens; just log and continue
            print(f"[WARN] is_registration_open() failed: {e}")

        if not selected_rows:
            # No selection -> button disabled
            self.ui.buttonViewSections.setEnabled(False)
            return

        # Check prerequisite eligibility for EVERY selected course
        for row_index in selected_rows:
            code_item = table.item(row_index.row(), 1)
            if not code_item:
                self.ui.buttonViewSections.setEnabled(False)
                return

            code = code_item.text()
            course = next(
                (c for c in self.all_courses if c["course_code"] == code),
                None
            )

            # If any selected course CANNOT be registered -> disable button
            if not course or not course["can_register"]:
                self.ui.buttonViewSections.setEnabled(False)
                return

        # All selected courses are allowed and registration is open
        self.ui.buttonViewSections.setEnabled(True)


    # ============================
    # VIEW SECTIONS FOR SELECTED COURSES
    # ============================
    def handle_view_sections(self):
        """
        Open modal dialog with sections for ALL selected courses.
        """
        table = self.ui.tableAllCourses
        selected_rows = table.selectionModel().selectedRows()

        if not selected_rows:
            return

        # Extract codes for all selected courses
        course_codes = [
            table.item(r.row(), 1).text()
            for r in selected_rows
        ]

        # Create modal dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("View Sections")
        dialog.setModal(True)

        # Layout for sections widget
        layout = QtWidgets.QVBoxLayout(dialog)

        # Create sections widget with multiple courses
        sections_widget = ViewSectionsWidget(
            student_id=self.student_utils.student_id,
            semester=self.semester,
            course_codes=course_codes,
            parent=dialog
        )

        layout.addWidget(sections_widget)

        dialog.resize(900, 600)
        dialog.exec()


# ---------------- Run standalone ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    student_id = 2500001
    semester = "First"
    window = RegisterCoursesWidget(student_id, semester)
    window.show()
    sys.exit(app.exec())
