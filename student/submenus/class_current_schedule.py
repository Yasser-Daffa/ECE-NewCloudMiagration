import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QWidget, QApplication, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

from student.class_student_utilities import StudentUtilities
from admin.class_admin_utilities import AdminUtilities

from app_ui.student_ui.submenus_ui.ui_current_schedule import Ui_CurrentSchedule



class CurrentScheduleWidget(QWidget):
    def __init__(self, student_utils, admin_utils, parent=None):
        super().__init__(parent)
        self.ui = Ui_CurrentSchedule()
        self.ui.setupUi(self)
        
        self.student_utils = student_utils
        self.admin_utils = admin_utils
        self.db = student_utils.db

        self.registered_courses = []

        # Add Refresh button
        self.ui.buttonRefresh.clicked.connect(self.load_registered_courses)

        # Disable remove button initially
        self.ui.buttonRemoveSelected.setEnabled(False)
        self.ui.buttonRemoveSelected.clicked.connect(self.remove_selected_courses)

        # Configure table for row selection
        table = self.ui.tableCourses
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.MultiSelection)

        # Connect selection change to button enable/disable
        table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Load registered courses
        self.load_registered_courses()
        self.format_table()

    def load_registered_courses(self):
        """Load courses registered by the student into the table."""
        self.registered_courses = self.student_utils.get_registered_courses_full()

        # Debug: see what is returned
        print("[DEBUG] Registered courses:", self.registered_courses)

        table = self.ui.tableCourses
        table.setRowCount(len(self.registered_courses))

        for row, course in enumerate(self.registered_courses):
            table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            table.setItem(row, 1, QTableWidgetItem(course.get("course_id", "")))
            table.setItem(row, 2, QTableWidgetItem(str(course.get("credit", ""))))
            table.setItem(row, 3, QTableWidgetItem(str(course.get("section", ""))))
            table.setItem(row, 4, QTableWidgetItem(course.get("days", "")))
            table.setItem(row, 5, QTableWidgetItem(course.get("time", "")))
            table.setItem(row, 6, QTableWidgetItem(course.get("room", "")))
            table.setItem(row, 7, QTableWidgetItem(course.get("instructor", "")))

        self.ui.buttonRemoveSelected.setEnabled(False)


    def format_table(self):
        table = self.ui.tableCourses

        # These must match the actual column order in our UI file:
        headers = [
            "#",           # 0 (row number)
            "Course",      # 1
            "Credits",     # 2
            "Section",     # 3
            "Days",        # 4
            "Time",        # 5
            "Room",        # 6
            "Instructor"   # 7
        ]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # Allow user to resize columns
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Recommended column widths (based on typical content)
        table.setColumnWidth(0, 60)     # row #
        table.setColumnWidth(1, 160)    # course code
        table.setColumnWidth(2, 80)     # credits
        table.setColumnWidth(3, 80)     # section #
        table.setColumnWidth(4, 170)    # days (ex: Sun-Tue)
        table.setColumnWidth(5, 160)    # time
        table.setColumnWidth(6, 200)    # room
        table.setColumnWidth(7, 120)    # instructor

        # Table behavior
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.MultiSelection)
        table.verticalHeader().setVisible(False)

        # row height
        table.verticalHeader().setDefaultSectionSize(60)

        # Enable sorting
        table.setSortingEnabled(True)


    def on_selection_changed(self):
        """Enable/disable Remove button based on row selection and global registration lock."""
        table = self.ui.tableCourses
        selected = table.selectionModel().selectedRows()

        # If global registration is closed, always disable the button
        try:
            if not self.student_utils.db.is_registration_open():
                self.ui.buttonRemoveSelected.setEnabled(False)
                self.ui.buttonRemoveSelected.setToolTip(
                    "Course add/drop period is currently closed."
                )
                return
            else:
                # Clear tooltip when registration is open
                self.ui.buttonRemoveSelected.setToolTip(
                    "Remove the selected registered sections from the student's schedule."
                )
        except Exception as e:
            # Do not crash if anything goes wrong with the check
            print(f"[WARN] is_registration_open() failed: {e}")

        # Normal behavior: enabled only when at least one row is selected
        self.ui.buttonRemoveSelected.setEnabled(bool(selected))


    def remove_selected_courses(self):
        """Remove selected courses from database and table."""
        table = self.ui.tableCourses
        selected_rows = sorted([idx.row() for idx in table.selectionModel().selectedRows()], reverse=True)

        for row in selected_rows:
            course_id = table.item(row, 1).text()
            self.student_utils.remove_registered_course(course_id)
            table.removeRow(row)

        # Re-number "#" column
        for i in range(table.rowCount()):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

        self.ui.buttonRemoveSelected.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from student.class_student_utilities import StudentUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    student_utils = StudentUtilities(db, 2500001)
    admin_utils = AdminUtilities(db)

    w = CurrentScheduleWidget(student_utils, admin_utils)

    w.show()
    sys.exit(app.exec())




