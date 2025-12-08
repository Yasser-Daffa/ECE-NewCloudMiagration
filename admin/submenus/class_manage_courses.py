#manage_courses.py

import os, sys, functools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_manage_courses import Ui_ManageCourses
from app_ui.admin_ui.submenus_ui.ui_add_courses_dialog import Ui_AddCourseDialog 
from admin.submenus.class_add_courses import AddCoursesDialog

from helper_files.shared_utilities import BaseLoginForm



class ManageCoursesController:

    def __init__(self, ui, admin_utils):
        self.ui = ui
        self.admin_utils = admin_utils
        self.db = admin_utils.db   # <-- now DB is accessible
        self.courses_data = []
        self.blf = BaseLoginForm()

        self.connect_ui_signals()
        self.load_courses()
        self.format_table()

    # ------------------ SIGNALS ------------------
    def connect_ui_signals(self):
        self.ui.lineEditSearch.textChanged.connect(self.search_courses)
        self.ui.buttonRemoveCourse.clicked.connect(self.remove_selected_courses)
        self.ui.buttonRefresh.clicked.connect(self.handle_refresh)
        self.ui.buttonAddCourse.clicked.connect(self.handle_add_course_clicked)
        self.ui.tableAllCourses.selectionModel().selectionChanged.connect(lambda: self.update_remove_button_text())

    # ------------------ REFRESH ------------------
    def handle_refresh(self):
        BaseLoginForm.animate_label_with_dots(
            self.ui.labelTotalCoursesCount,
            base_text="Refreshing",
            interval=400,
            duration=2000,
            on_finished=self.load_courses
        )

    # ------------------ LOAD COURSES ------------------
    def load_courses(self):
        self.courses_data.clear()
        self.ui.tableAllCourses.setRowCount(0)

        rows = self.db.ListCourses()  # expected: (code, name, credits)

        for i, row in enumerate(rows, start=1):
            course = {
                "row_number": i,
                "code": row[0],
                "name": row[1],
                "credits": row[2]
            }
            self.courses_data.append(course)

        self.fill_table(self.courses_data)
        self.update_total_counter()

    # ------------------ POPULATE TABLE ------------------
    def fill_table(self, courses):
        table = self.ui.tableAllCourses
        table.setRowCount(len(courses))

        for row_idx, course in enumerate(courses):
            # Row number
            item_number = QTableWidgetItem(str(row_idx + 1))
            item_number.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 0, item_number)

            # Course Code
            code_item = QTableWidgetItem(course["code"])
            code_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 1, code_item)

            # Name
            name_item = QTableWidgetItem(course["name"])
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 2, name_item)

            # Credits
            credits_item = QTableWidgetItem(str(course["credits"]))
            credits_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 3, credits_item)

            # Remove button
            btnRemove = QPushButton("Remove")
            btnRemove.setMinimumWidth(70)
            btnRemove.setMinimumHeight(30)
            btnRemove.setStyleSheet(
                "QPushButton {background-color:#f8d7da; color:#721c24; border-radius:5px; padding:4px;} "
                "QPushButton:hover {background-color:#c82333; color:white;}"
            )
            btnRemove.clicked.connect(functools.partial(self.remove_single_course, course["code"]))

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            layout.addWidget(btnRemove)

            table.setSortingEnabled(True)
            table.setCellWidget(row_idx, 4, container)

    # ------------------ FORMAT TABLE ------------------
    def format_table(self):
        table = self.ui.tableAllCourses

        headers = ["#", "Course Code", "Name", "Credits", "Actions"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # row selection mode (recommended)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # spacing & sizes
        table.verticalHeader().setDefaultSectionSize(80)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 200)
        table.setColumnWidth(2, 350)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 120)

        # make header interactive/resizable
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

    # ------------------ SEARCH ------------------
    def search_courses(self):
        text = self.ui.lineEditSearch.text().lower()
        filtered = [
            c for c in self.courses_data
            if text in c["code"].lower() or text in c["name"].lower()
        ]
        self.fill_table(filtered)

    # ------------------ REMOVE SINGLE ------------------
    def remove_single_course(self, code):
        reply = self.blf.show_confirmation(
            "Delete Course",
            f"Are you sure you want to delete course '{code}'?"
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.DeleteCourse(code)
            self.load_courses()

    # ------------------ REMOVE SELECTED ------------------
    def get_selected_course_codes(self):
        """
        Uses row selection instead of checkboxes.
        """
        table = self.ui.tableAllCourses
        selected_rows = table.selectionModel().selectedRows()

        codes = []
        for idx in selected_rows:
            row = idx.row()
            codes.append(table.item(row, 1).text())  # column 1 = course code

        return codes

    def remove_selected_courses(self):
        selected = self.get_selected_course_codes()

        if not selected:
            reply = self.blf.show_confirmation(
                "Delete All Courses",
                "No rows selected.\nDelete ALL courses?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            self.db.cur.execute("DELETE FROM courses")
            self.db.commit()
            self.load_courses()
            return

        reply = self.blf.show_confirmation(
            "Delete Selected Courses",
            f"Delete {len(selected)} selected course(s)?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for code in selected:
            self.db.DeleteCourse(code)

        self.load_courses()

    # ---------------- UPDATE REMOVE BUTTON TEXT PER SELECTION -----------
    def update_remove_button_text(self):
        selected = len(self.ui.tableAllCourses.selectionModel().selectedRows())

        if selected == 0:
            self.ui.buttonRemoveCourse.setText("Remove All")
        else:
            self.ui.buttonRemoveCourse.setText(f"Remove Selected ({selected})")

    # ------------------ TOTAL COUNTER ------------------
    def update_total_counter(self):
        self.ui.labelTotalCoursesCount.setText(
            f"Total Courses: {len(self.courses_data)}"
        )
    # ------------------ ADD COURSE ------------------
    def handle_add_course_clicked(self):
        # Open our existing AddCoursesDialog
        dialog = AddCoursesDialog(self.admin_utils)  # pass your admin/db object
        dialog.exec()
        self.load_courses()  # refresh table after a course is added



# ---------------- Testings ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    

    from admin.class_admin_utilities import AdminUtilities
    from database_files.class_database_uitlities import DatabaseUtilities
    from database_files.cloud_database import get_pooled_connection

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    admin_utils = AdminUtilities(db)


    window = QWidget()
    ui = Ui_ManageCourses()
    ui.setupUi(window)  

    controller = ManageCoursesController(ui, admin_utils)

    window.show()
    sys.exit(app.exec())
