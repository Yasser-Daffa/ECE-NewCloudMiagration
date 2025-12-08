import os
import sys
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.student_ui.submenus_ui.ui_view_program_plans import Ui_ViewProgramPlans
from helper_files.shared_utilities import BaseLoginForm
from admin.class_admin_utilities import AdminUtilities


class ViewProgramPlansWidget(QWidget):
    """
    Student read-only program plan viewer.
    Uses AdminUtilities → list_plan_courses() to load all data.
    """

    def __init__(self, student_utils, admin_utils, parent=None):
        super().__init__(parent)

        self.ui = Ui_ViewProgramPlans()
        self.ui.setupUi(self)
        self.blf = BaseLoginForm()

        self.student_utils = student_utils
        self.admin_utils = admin_utils
        self.db = student_utils.db

        self.all_rows = []  # will hold (program, code, name, credits, level)

        self.setup_programs_combo()
        self.setup_levels_combo()

        # Connect combos
        self.ui.buttonRefresh.clicked.connect(self.load_plans)
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.load_plans)
        self.ui.comboBoxLevel.currentIndexChanged.connect(self.load_plans)

        # Empty at start until program selected
        self.fill_table([])
        self.format_table()


    # ----------------- إعداد الكمبوبوكس -----------------

    def setup_programs_combo(self):
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
            cb.addItem(f"{code} - {label}", code)


    def setup_levels_combo(self):
        cb = self.ui.comboBoxLevel
        cb.clear()
        cb.addItem("All Levels", None)
        for lvl in range(1, 9):
            cb.addItem(f"Level {lvl}", lvl)


    # ----------------- تحميل وفلترة وترتيب -----------------

    def load_plans(self):
        program_code = self.ui.comboBoxSelectProgram.currentData()

        if program_code is None:
            self.fill_table([])
            return

        # Load program rows
        rows = self.admin_utils.db.list_plan_courses(program_code)
        self.all_rows = rows

        # Level filter
        level_filter = self.ui.comboBoxLevel.currentData()
        if level_filter is not None:
            rows = [r for r in rows if r[4] == level_filter]

        # Sort by level
        rows.sort(key=lambda r: r[4])

        self.fill_table(rows)


    def fill_table(self, rows):
        table = self.ui.tableAllCourses
        table.setRowCount(len(rows))

        for i, (program, code, name, credits, level) in enumerate(rows):

            item0 = QTableWidgetItem(str(i + 1))     # #
            item0.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 0, item0)

            item1 = QTableWidgetItem(str(level))     # LEVEL
            item1.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 1, item1)

            item2 = QTableWidgetItem(code)           # CODE
            item2.setData(Qt.ItemDataRole.UserRole, program)
            item2.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 2, item2)

            item3 = QTableWidgetItem(name)           # NAME
            item3.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 3, item3)

            item4 = QTableWidgetItem(str(credits))   # CREDITS
            item4.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 4, item4)

            item5 = QTableWidgetItem("-")             # PREREQS (empty)
            item5.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 5, item5)



    def format_table(self):
        table = self.ui.tableAllCourses

        # Get all headers from the table itself instead of assigning
        headers = [
            table.horizontalHeaderItem(col).text()
            for col in range(table.columnCount())
        ]
        

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # Resize behavior — same style as ManageCourses / ManageFaculty
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Default column widths (adjusted for your content)
        table.setColumnWidth(0, 60)    # Row #
        table.setColumnWidth(1, 80)    # Level
        table.setColumnWidth(2, 160)   # Code
        table.setColumnWidth(3, 300)   # Name
        table.setColumnWidth(4, 90)    # Credits
        table.setColumnWidth(5, 250)   # Prerequisites

        # Table behavior — consistent across admin UI
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        table.verticalHeader().setDefaultSectionSize(60)
        table.setSortingEnabled(True)


# Standalone Test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    from admin.class_admin_utilities import db

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from student.class_student_utilities import StudentUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    student_utils = StudentUtilities(db, 2500001)
    admin_utils = AdminUtilities(db)

    w = ViewProgramPlansWidget(student_utils, admin_utils)
    w.show()

    sys.exit(app.exec())


