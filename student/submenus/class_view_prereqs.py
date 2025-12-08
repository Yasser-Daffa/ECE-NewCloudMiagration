import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

from app_ui.student_ui.submenus_ui.ui_view_prereqs import Ui_ViewPrereqs
from admin.class_admin_utilities import AdminUtilities
from helper_files.shared_utilities import BaseLoginForm


class ViewPrereqsWidget(QWidget):
    """
    Student read-only prereq viewer.
    Shows:
        Course Code
        Course Name
        Prerequisites (comma separated)
    """

    def __init__(self, student_utils, admin_utils, parent=None):
        super().__init__(parent)

        self.ui = Ui_ViewPrereqs()
        self.ui.setupUi(self)

        self.student_utils = student_utils
        self.admin_utils = admin_utils
        self.db = student_utils.db

        self.blf = BaseLoginForm()
        self.courses_data = []

        # signals
        self.ui.lineEditSearch.textChanged.connect(self.search_courses)
        self.ui.buttonRefresh.clicked.connect(self.load_courses)

        # initial load
        self.load_courses()
        self.format_table()

    # ---------------------------------------------------------
    # Load course → prereq data
    # ---------------------------------------------------------
    def load_courses(self):
        self.courses_data.clear()
        table = self.ui.tableAllCourses
        table.setRowCount(0)

        rows = self.admin_utils.list_courses()     # (code, name, credits)

        for i, row in enumerate(rows, start=1):
            code = str(row[0]).strip()
            name = row[1]

            prereqs = self.admin_utils.list_prerequisites(code)
            prereq_str = ", ".join(prereqs)

            self.courses_data.append({
                "row": i,
                "code": code,
                "name": name,
                "prereq": prereq_str
            })

        self.fill_table(self.courses_data)
        self.update_counter()

    # ---------------------------------------------------------
    # Fill table
    # ---------------------------------------------------------
    def fill_table(self, data):
        table = self.ui.tableAllCourses
        table.setRowCount(len(data))

        for row_idx, c in enumerate(data):

            item0 = QTableWidgetItem(str(row_idx + 1))      # #
            item0.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 0, item0)

            item1 = QTableWidgetItem(c["code"])            # code
            item1.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row_idx, 1, item1)

            item2 = QTableWidgetItem(c["name"])            # name
            item2.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row_idx, 2, item2)

            item3 = QTableWidgetItem(c["prereq"])          # prereqs
            item3.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row_idx, 3, item3)

    # ---------------------------------------------------------
    # Format (read-only student style)
    # ---------------------------------------------------------
    def format_table(self):
        table = self.ui.tableAllCourses
        headers = ["#", "Course Code", "Course Name", "Prerequisites"]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # default widths
        table.setColumnWidth(0, 60)     # row #
        table.setColumnWidth(1, 160)    # code
        table.setColumnWidth(2, 300)    # name
        table.setColumnWidth(3, 260)    # prereqs

        # behavior
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        table.setSortingEnabled(True)
        table.verticalHeader().setDefaultSectionSize(55)

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------
    def search_courses(self):
        t = self.ui.lineEditSearch.text().lower().strip()

        filtered = [
            c for c in self.courses_data
            if t in c["code"].lower()
            or t in c["name"].lower()
            or t in c["prereq"].lower()
        ]

        self.fill_table(filtered)

    # ---------------------------------------------------------
    # Counter text
    # ---------------------------------------------------------
    def update_counter(self):
        self.ui.labelTotalCoursesCount.setText(f"{len(self.courses_data)} Courses Total")


# Standalone test
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from student.class_student_utilities import StudentUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    student_utils = StudentUtilities(db, 2500001)
    admin_utils = AdminUtilities(db)

    w = ViewPrereqsWidget(student_utils, admin_utils)


    w.show()
    sys.exit(app.exec())
