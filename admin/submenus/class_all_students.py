import os, sys, functools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_all_students import Ui_AllStudents
from helper_files.shared_utilities import BaseLoginForm
from admin.class_admin_utilities import AdminUtilities


class AllStudentsController:
    """
    Controller for the All Students page.
    Handles:
    - Loading active students
    - Filtering by search or program
    - Removing students individually or in bulk
    - Updating table formatting
    """

    def __init__(self, ui: Ui_AllStudents, admin_utils: AdminUtilities):
        self.ui = ui
        self.admin_utils = admin_utils               # admin object (business logic)
        self.db = admin_utils.db               # DatabaseUtilities instance

        self.students_data = []                # Holds all active students
        self.blf = BaseLoginForm()             # For confirmations and animations

        # Connect UI signals
        self.connect_ui_signals()

        # Initial load
        self.load_students()
        self.format_table()

    # ----------------- UI SIGNAL CONNECTIONS -----------------
    def connect_ui_signals(self):
        # Search filter (name / id / email / program)
        self.ui.lineEditSearch.textChanged.connect(self.search_and_filter)

        # Program filter from combo box
        self.ui.comboBoxSelectProgram.currentIndexChanged.connect(self.search_and_filter)

        # Remove selected button
        self.ui.buttonRemoveSelected.clicked.connect(self.remove_selected_students)

        # Refresh button
        self.ui.buttonRefresh.clicked.connect(self.handle_refresh)

        # Enable/disable "Remove Selected" button depending on table selection
        self.ui.tableAllStudents.selectionModel().selectionChanged.connect(
            lambda: self.update_remove_button_text()
        )

        # Trigger refresh animation + student loading on first run
        self.handle_refresh()

    # ----------------- LOAD / POPULATE TABLE -----------------
    def load_students(self):
        """
        Load all active students from the database into self.students_data
        and then populate the table.
        """
        self.students_data.clear()
        self.ui.tableAllStudents.setRowCount(0)

        rows = self.db.list_users()
        # row format: (user_id, name, email, program, state, account_status, password_h)

        # Filter only ACTIVE students with state = "student"
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
                "program": row[3],       # may be None
                "state": row[4],
                "account_status": row[5],
            }
            self.students_data.append(student)

        # Display full table with all active students
        self.fill_table(self.students_data)
        self.update_total_counter()
        self.update_remove_button_text()

    def handle_refresh(self):
        """
        Shows a loading animation on the label and refreshes students afterward.
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
        Sets column widths and table formatting for a clean layout.
        """
        table = self.ui.tableAllStudents
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(80)

        # Column widths
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 120)
        table.setColumnWidth(2, 220)
        table.setColumnWidth(3, 260)
        table.setColumnWidth(4, 100)
        table.setColumnWidth(5, 120)
        table.setColumnWidth(6, 120)
        table.setColumnWidth(7, 80)

    # ----------------- POPULATE TABLE -----------------
    def fill_table(self, students):
        """
        Populate the table widget with a list of student dictionaries.
        """
        table = self.ui.tableAllStudents
        table.setRowCount(len(students))

        for row_idx, student in enumerate(students):
            # 0: Row number
            item_number = QTableWidgetItem(str(row_idx + 1))
            item_number.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 0, item_number)

            # 1: Student ID
            item_id = QTableWidgetItem(str(student["user_id"]))
            item_id.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row_idx, 1, item_id)

            # 2: Name
            table.setItem(row_idx, 2, QTableWidgetItem(student["name"] or ""))

            # 3: Email
            table.setItem(row_idx, 3, QTableWidgetItem(student["email"] or ""))

            # 4: Program (handles None)
            prog_text = student["program"] or ""
            table.setItem(row_idx, 4, QTableWidgetItem(prog_text))

            # 5: State
            table.setItem(row_idx, 5, QTableWidgetItem(student["state"] or ""))

            # 6: Remove Student button
            btnRemove = QPushButton("Remove")
            btnRemove.setMinimumWidth(70)
            btnRemove.setMinimumHeight(30)
            btnRemove.setStyleSheet(
                "QPushButton {background-color:#f8d7da; color:#721c24; border-radius:5px; padding:4px;} "
                "QPushButton:hover {background-color:#c82333; color:white;}"
            )
            btnRemove.clicked.connect(
                functools.partial(self.remove_student, student["user_id"])
            )

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            layout.addWidget(btnRemove)
            table.setCellWidget(row_idx, 6, container)

    # ----------------- SEARCH + PROGRAM FILTER -----------------
    def search_and_filter(self):
        """
        Applies both text filter and program filter simultaneously.

        Text filter checks:
            - name
            - user id
            - email
            - program

        Program filter checks selected program from combo box.
        """
        text = self.ui.lineEditSearch.text().strip().lower()
        program_filter = self.ui.comboBoxSelectProgram.currentText()

        # Mapping user-friendly names to program codes used in DB
        program_map = {
            "Computer": "COMP",
            "Communication": "COMM",
            "Power": "PWM",
            "Biomedical": "BIO",
        }

        # Program filter logic
        def match_program(s):
            if program_filter == "All Programs":
                return True
            code = program_map.get(program_filter)
            return (s["program"] or "") == code

        # Text filter logic
        def match_text(s):
            if not text:
                return True

            name = (s["name"] or "").lower()
            email = (s["email"] or "").lower()
            program_str = (s["program"] or "").lower()
            user_id_str = str(s["user_id"])

            return (
                text in name
                or text in user_id_str
                or text in email
                or text in program_str
            )

        filtered = [
            s for s in self.students_data
            if match_program(s) and match_text(s)
        ]

        self.fill_table(filtered)

    # ----------------- REMOVE INDIVIDUAL STUDENT -----------------
    def remove_student(self, user_id):
        reply = self.blf.show_confirmation(
            "Remove Student",
            f"Are you sure you want to remove student ID {user_id}?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            msg = self.admin_utils.admin_delete_student(user_id)
            print(msg)
            self.load_students()

    # ----------------- REMOVE SELECTED STUDENTS -----------------
    def get_selected_user_ids(self):
        """
        Returns a list of selected student IDs from the table.
        """
        table = self.ui.tableAllStudents
        selected_rows = table.selectionModel().selectedRows()

        ids = []
        for idx in selected_rows:
            item = table.item(idx.row(), 1)  # Column 1 is the student ID
            if item:
                try:
                    ids.append(int(item.text()))
                except ValueError:
                    # Ignore unexpected non-numeric values
                    continue
        return ids

    def remove_selected_students(self):
        """
        Removes:
        - All students if none are selected
        - Selected students if at least one row is selected
        """
        selected_ids = self.get_selected_user_ids()

        # No selected rows → ask to remove all
        if not selected_ids:
            reply = self.blf.show_confirmation(
                "Remove All Students",
                "Are you sure you want to remove all students?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            msg = self.admin_utils.admin_delete_all_students()
            print(msg)
            self.load_students()
            return

        # Removing selected rows
        reply = self.blf.show_confirmation(
            "Remove Selected Students",
            f"Are you sure you want to remove {len(selected_ids)} selected student(s)?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for uid in selected_ids:
            self.admin_utils.admin_delete_student(uid)

        self.load_students()

    # ----------------- UPDATE REMOVE BUTTON TEXT -----------------
    def update_remove_button_text(self):
        """
        Updates the Remove Selected button:
        - Disabled when no rows selected
        - Shows count when rows selected
        """
        selected_count = len(self.ui.tableAllStudents.selectionModel().selectedRows())

        if selected_count == 0:
            self.ui.buttonRemoveSelected.setText("Remove Selected")
            self.ui.buttonRemoveSelected.setEnabled(False)
        else:
            self.ui.buttonRemoveSelected.setText(f"Remove Selected ({selected_count})")
            self.ui.buttonRemoveSelected.setEnabled(True)

    # ----------------- UPDATE TOTAL STUDENT COUNTER -----------------
    def update_total_counter(self):
        """
        Updates the label that shows how many students are loaded.
        """
        self.ui.labelTotalStudentsCount.setText(f"Total Students: {len(self.students_data)}")


# ---------------- MAIN APP (for standalone testing only) ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)


    window = QWidget()
    ui = Ui_AllStudents()
    ui.setupUi(window)

    controller = AllStudentsController(ui, admin_utils)

    window.show()
    sys.exit(app.exec())
