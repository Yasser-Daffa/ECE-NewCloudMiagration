# admin/submenus/class_manage_faculty.py

import os, sys, functools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QDialog
)
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_manage_faculty import Ui_ManageFaculty
from helper_files.shared_utilities import BaseLoginForm, warning, info
from login_files.create_account_for_admin import SignupAndConfirmWindow


class ManageFacultyWidget(QWidget):
    """
    Manage admins:
    - Uses Ui_ManageFaculty
    - No raw SQL here
    - Uses list_users() and delete_user()
    - Add Admin uses SignupAndConfirmWindow
    - No actions column inside the table
    """

    def __init__(self, admin_utils, parent=None):
        super().__init__(parent)

        self.ui = Ui_ManageFaculty()
        self.ui.setupUi(self)
        # Setup admin utils connection with db
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        self.blf = BaseLoginForm()
        self.admins_data = []

        self.ui.buttonAddFaculty.setEnabled(True)

        # Connections
        self.ui.lineEditSearch.textChanged.connect(self.search_admins)
        self.ui.buttonRefresh.clicked.connect(self.load_admins)
        self.ui.buttonRemoveSelected.clicked.connect(self.remove_selected_admins)
        self.ui.buttonAddFaculty.clicked.connect(self.add_new_admin)

        self.format_table()
        self.load_admins()

        # Track selection changes
        self.ui.tableFaculty.selectionModel().selectionChanged.connect(
            lambda *_: self.update_remove_button_state()
        )
        self.update_remove_button_state()

    # -------------------------------------------------------------
    # TABLE SETUP (Actions column removed)
    # -------------------------------------------------------------
    def format_table(self):
        table = self.ui.tableFaculty
        headers = ["#", "Admin ID", "Name", "Email", "State"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    # -------------------------------------------------------------
    # LOAD ADMINS
    # -------------------------------------------------------------
    def load_admins(self):
        self.admins_data.clear()
        self.ui.tableFaculty.setRowCount(0)

        rows = self.db.list_users()  # (id, name, email, program, state, status)

        active_admin_rows = [
            row for row in rows
            if len(row) >= 6 and row[4] == "admin" and row[5] == "active"
        ]

        for i, row in enumerate(active_admin_rows, start=1):
            admin = {
                "row_number": i,
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "program": row[3],
                "state": row[4],
                "account_status": row[5],
            }
            self.admins_data.append(admin)

        self.fill_table(self.admins_data)
        self.update_total_count()
        self.update_remove_button_state()

    # -------------------------------------------------------------
    # FILL TABLE and FORMAT TABLE
    # -------------------------------------------------------------
    def fill_table(self, admins):
        table = self.ui.tableFaculty
        table.setRowCount(len(admins))

        for row_idx, admin in enumerate(admins):
            table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            table.setItem(row_idx, 1, QTableWidgetItem(str(admin["user_id"])))
            table.setItem(row_idx, 2, QTableWidgetItem(admin["name"]))
            table.setItem(row_idx, 3, QTableWidgetItem(admin["email"]))
            table.setItem(row_idx, 4, QTableWidgetItem(admin["state"]))


    def format_table(self):
        table = self.ui.tableFaculty
        headers = ["#", "Admin ID", "Name", "Email", "State"]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # Column resize behavior (interactive like ManageCourses)
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Optional: define sensible default widths
        table.setColumnWidth(0, 40)   # row number
        table.setColumnWidth(1, 120)  # admin ID
        table.setColumnWidth(2, 260)  # name
        table.setColumnWidth(3, 330)  # email
        table.setColumnWidth(4, 120)  # state

        # General table behavior
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        table.setSortingEnabled(True)
        table.verticalHeader().setDefaultSectionSize(60)


    # -------------------------------------------------------------
    # SEARCH
    # -------------------------------------------------------------
    def search_admins(self):
        text = self.ui.lineEditSearch.text().lower().strip()
        if not text:
            self.fill_table(self.admins_data)
            return

        filtered = [
            a for a in self.admins_data
            if text in a["name"].lower() or text in str(a["user_id"])
        ]
        self.fill_table(filtered)

    # -------------------------------------------------------------
    # REMOVE ADMINS
    # -------------------------------------------------------------
    def get_selected_admin_ids(self):
        table = self.ui.tableFaculty
        selected_rows = table.selectionModel().selectedRows()
        ids = []
        for idx in selected_rows:
            item = table.item(idx.row(), 1)
            if item:
                try:
                    ids.append(int(item.text()))
                except ValueError:
                    pass
        return ids

    def remove_selected_admins(self):
        ids = self.get_selected_admin_ids()
        if not ids:
            warning(self, "No admins selected.")
            return

        reply = self.blf.show_confirmation(
            "Remove Admins",
            f"Remove {len(ids)} selected admin accounts?"
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        for uid in ids:
            self.db.delete_user(uid)

        info(self, f"Removed {len(ids)} admin accounts.")
        self.load_admins()

    # -------------------------------------------------------------
    # ADD ADMIN
    # -------------------------------------------------------------
    def add_new_admin(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Admin")
        dialog.setModal(True)
        dialog.resize(600, 900)

        # Prevent dialog from overriding child stylesheets
        dialog.setStyleSheet("background: qlineargradient(x1:0, y1:0,x2:1, y2:1,stop:0 #f093fb,stop:1 #f5576c);")

        layout = QVBoxLayout(dialog)
        signup_widget = SignupAndConfirmWindow(
            admin_utils=self.admin_utils,   # <-- correct object
            parent=dialog             # <-- optional
        )

        layout.addWidget(signup_widget)

        signup_widget.destroyed.connect(lambda *_: self.load_admins())
        dialog.exec()

    # -------------------------------------------------------------
    # UI HELPERS
    # -------------------------------------------------------------
    def update_remove_button_state(self):
        model = self.ui.tableFaculty.selectionModel()
        has_selection = model is not None and model.hasSelection()
        self.ui.buttonRemoveSelected.setEnabled(has_selection)

    def update_total_count(self):
        self.ui.labelTotalCount.setText(f"{len(self.admins_data)} Total Admins")


# Standalone test
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    
    from admin.class_admin_utilities import AdminUtilities
    from database_files.class_database_uitlities import DatabaseUtilities
    from database_files.cloud_database import get_pooled_connection

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    window = ManageFacultyWidget(admin_utils)
    window.show()
    sys.exit(app.exec())
