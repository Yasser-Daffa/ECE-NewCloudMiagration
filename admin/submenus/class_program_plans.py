import os
import sys

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.admin_ui.submenus_ui.ui_program_plans import Ui_ProgramPlans
from helper_files.shared_utilities import BaseLoginForm, warning, info, error


class ProgramPlansWidget(QWidget):
    """
    Manages courses inside academic program plans.
    Features:
    - Load courses for a specific program
    - Filter by level
    - Add course to plan
    - Remove one or multiple courses from the plan
    """

    def __init__(self, admin_utils, parent=None):
        super().__init__(parent)
        self.ui = Ui_ProgramPlans()
        self.ui.setupUi(self)
        self.blf = BaseLoginForm()
    
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        self.all_rows = []  # Each row is (program, code, name, credits, level)

        # Setup program and level combo boxes
        self.setup_programs_combo()
        self.setup_levels_combo()

        # Connect buttons
        self.ui.buttonRefresh.clicked.connect(self.load_plans)
        self.ui.buttonAddCourse.clicked.connect(self.on_add_course_clicked)
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.load_plans)
        self.ui.comboBoxStatusFilter.currentIndexChanged.connect(self.load_plans)
        self.ui.buttonEdit.clicked.connect(self.on_edit_plan_clicked)

        table = self.ui.tableAllCourses
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.MultiSelection)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)

        # Update remove button as selection changes
        table.selectionModel().selectionChanged.connect(self.update_remove_button)
        self.ui.buttonRemoveCourse.setEnabled(False)

        # Table initially empty until program is selected
        self.fill_table([])
        self.format_table()

    # ----------------- Setup ComboBoxes -----------------

    def setup_programs_combo(self):
        """Populates program selection combo box."""
        cb = self.ui.comboBoxSelectProgram
        cb.clear()
        cb.addItem("Select program...", None)  # Nothing shown until program is chosen

        programs = [
            ("PWM",  "Power & Machines Engineering"),
            ("BIO",  "Biomedical Engineering"),
            ("COMM", "Communications Engineering"),
            ("COMP", "Computer Engineering"),
        ]
        for code, label in programs:
            cb.addItem(f"{code} - {label}", code)

    def setup_levels_combo(self):
        """Populates levels filter combo box."""
        cb = self.ui.comboBoxStatusFilter
        cb.clear()
        cb.addItem("All Levels", None)
        for lvl in range(1, 9):
            cb.addItem(f"Level {lvl}", lvl)

    # ----------------- Load and Filter -----------------

    def load_plans(self):
        """
        Loads all plan courses for the selected program.
        Applies level filter if selected.
        """
        program_code = self.ui.comboBoxSelectProgram.currentData()

        # Do not display anything if program not selected
        if program_code is None:
            self.all_rows = []
            self.fill_table([])
            return

        # Load all plan courses for the program
        rows = self.admin_utils.db.list_plan_courses(program=program_code)
        self.all_rows = rows

        level_filter = self.ui.comboBoxStatusFilter.currentData()

        # Filter by level if needed
        if level_filter is not None:
            rows = [r for r in rows if r[4] == level_filter]  # r = (program, code, name, credits, level)

        # Sort by level
        rows.sort(key=lambda r: r[4])

        self.fill_table(rows)

    def fill_table(self, rows):
        """Fills the table with plan courses."""
        table = self.ui.tableAllCourses
        table.setRowCount(len(rows))

        for i, (program, code, name, credits, level) in enumerate(rows):
            # Row number
            item0 = QTableWidgetItem(str(i + 1))
            item0.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 0, item0)

            # Level
            item1 = QTableWidgetItem(str(level))
            item1.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 1, item1)

            # Course code (store program in UserRole)
            item2 = QTableWidgetItem(code)
            item2.setData(Qt.ItemDataRole.UserRole, program)
            item2.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 2, item2)

            # Course name
            item3 = QTableWidgetItem(name)
            item3.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 3, item3)

            # Credits
            item4 = QTableWidgetItem(str(credits))
            item4.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 4, item4)

            # Get prerequisites from DB
            prereqs = self.admin_utils.db.list_prerequisites(code)
            prereq_text = ", ".join(prereqs) if prereqs else "-"

            # Prerequisites 
            item5 = QTableWidgetItem(prereq_text)
            item5.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            table.setItem(i, 5, item5)


    def format_table(self):
        table = self.ui.tableAllCourses

        # These MUST match our UI column order
        headers = [
            "#",          # 0
            "Level",      # 1
            "Code",       # 2
            "Name",       # 3
            "Credits",    # 4
            "Prereqs",    # 5
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



    # ----------------- Delete Courses -----------------

    def on_delete_course_clicked(self):
        """
        Deletes selected course(s) from the plan.
        """
        table = self.ui.tableAllCourses
        selected_rows = table.selectionModel().selectedRows()

        if not selected_rows:
            warning(self, "Please select at least one course to delete.")
            return

        # Gather selected courses
        to_delete = []
        for idx in selected_rows:
            row = idx.row()
            course_item = table.item(row, 2)
            if course_item:
                code = course_item.text().strip()
                program = course_item.data(Qt.ItemDataRole.UserRole)
                to_delete.append((program, code))

        confirm = self.blf.show_confirmation(
            "Confirm Delete",
            f"Remove {len(to_delete)} selected course(s) from the plan?",
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Delete each selected course
        for program, course_code in to_delete:
            try:
                self.admin_utils.admin_delete_course_from_plan(program, course_code)
            except Exception as e:
                error(self, f"Error deleting {course_code}:\n{e}")

        self.load_plans()

    def update_remove_button(self):
        """
        Updates the remove button text depending on selected rows count.
        """
        table = self.ui.tableAllCourses
        n = len(table.selectionModel().selectedRows())

        if n > 0:
            self.ui.buttonRemoveCourse.setText(f"Remove Selected ({n})")
            self.ui.buttonRemoveCourse.setEnabled(True)
        else:
            self.ui.buttonRemoveCourse.setText("Remove Selected")
            self.ui.buttonRemoveCourse.setEnabled(False)

    # ----------------- Add Course to Plan -----------------

    def on_add_course_clicked(self):
        """Open AddCourseToPlan dialog."""
        from admin.submenus.class_add_course_to_plan import AddCourseToPlanDialog
        dialog = AddCourseToPlanDialog(self.admin_utils)
        dialog.exec()


    def on_edit_plan_clicked(self):
        table = self.ui.tableAllCourses
        selected = table.selectedIndexes()

        if not selected:
            warning(self, "Please select a course to edit.")
            return

        row = selected[0].row()

        program = table.item(row, 2).data(Qt.ItemDataRole.UserRole)
        course_code = table.item(row, 2).text().strip()
        level = int(table.item(row, 1).text())

        if level > 9:
            warning(None, "level cannot be more than 9")
            return

        from admin.submenus.class_edit_plan import EditCourseToPlanDialog
        dialog = EditCourseToPlanDialog(self.admin_utils, program, course_code, level)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)


    from database_files.class_database_uitlities import DatabaseUtilities
    from database_files.cloud_database import get_pooled_connection
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    w = ProgramPlansWidget(admin_utils)
    w.show()
    sys.exit(app.exec())
