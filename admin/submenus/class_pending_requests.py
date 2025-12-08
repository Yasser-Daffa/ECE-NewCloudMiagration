import os, sys, functools

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_pending_requests import Ui_PendingRequestsWidget
from helper_files.shared_utilities import BaseLoginForm, EmailSender
from admin.class_admin_utilities import AdminUtilities


class PendingRequestsController:
    """
    Controller for pending student approval requests.

    Uses only AdminUtilities (no raw SQL).
    Students are fetched using admin_list_pending_students(), which returns all
    inactive student accounts waiting for approval.

    Features:
        - Display pending student list
        - Search by name or ID
        - Approve or reject individual students
        - Approve or reject all or only selected students
        - Send email notification upon approval or rejection
    """

    def __init__(self, ui: Ui_PendingRequestsWidget, admin_utils: AdminUtilities):
        self.ui = ui
        self.admin = admin_utils               # AdminUtilities instance
        self.db = admin_utils.db

        self.students_data = []                # Cached list of pending students
        self.animate = BaseLoginForm.animate_label_with_dots
        self.blf = BaseLoginForm()
        self.es = EmailSender()                # Email sending helper

        # Bind UI events
        self.connect_ui_signals()

        # Load initial data
        self.load_pending_students()
        self.format_table()

        # Checkbox listener for enabling or disabling mass actions
        self.ui.tableRequests.itemChanged.connect(self.update_approve_reject_button_state)

    # ----------------------------------------------------------------------
    # SIGNAL CONNECTIONS
    # ----------------------------------------------------------------------
    def connect_ui_signals(self):
        if hasattr(self.ui, "lineEditSearch"):
            self.ui.lineEditSearch.textChanged.connect(self.search_students)

        if hasattr(self.ui, "btnApproveAll"):
            self.ui.btnApproveAll.clicked.connect(self.approve_selected_students)

        if hasattr(self.ui, "btnRejectAll"):
            self.ui.btnRejectAll.clicked.connect(self.reject_selected_students)

        # Load initially with refresh animation
        self.handle_refresh()
        self.ui.btnRefresh.clicked.connect(self.handle_refresh)

    # ----------------------------------------------------------------------
    # LOAD PENDING STUDENTS
    # ----------------------------------------------------------------------
    def load_pending_students(self):
        """
        Loads all pending students using AdminUtilities.
        Only inactive student accounts are returned.
        """
        self.students_data = self.admin.admin_list_pending_students()
        self.ui.tableRequests.setRowCount(0)
        self.fill_table(self.students_data)
        self.update_pending_counter()

    def handle_refresh(self):
        """
        Runs refresh animation then reloads data.
        """
        self.animate(
            self.ui.labelPendingCount,
            base_text="Refreshing",
            interval=400,
            duration=2000,
            on_finished=self.load_pending_students
        )

    # ----------------------------------------------------------------------
    # TABLE POPULATION
    # ----------------------------------------------------------------------
    def fill_table(self, students):
        """
        Populates the table widget with pending student information.
        """
        table = self.ui.tableRequests
        table.setRowCount(len(students))

        for row_idx, student in enumerate(students):
            # Row number
            item_number = QTableWidgetItem(str(row_idx + 1))
            item_number.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row_idx, 1, item_number)

            # Student ID
            table.setItem(row_idx, 2, QTableWidgetItem(str(student["user_id"])))

            # Student info columns
            table.setItem(row_idx, 3, QTableWidgetItem(student["name"]))
            table.setItem(row_idx, 4, QTableWidgetItem(student["email"]))
            table.setItem(row_idx, 5, QTableWidgetItem(student["program"] or ""))
            table.setItem(row_idx, 6, QTableWidgetItem(student["state"] or ""))

            # Approve button
            btnApprove = QPushButton("Approve")
            btnApprove.setMinimumWidth(70)
            btnApprove.setMinimumHeight(30)
            btnApprove.setStyleSheet(
                "QPushButton {background-color:#d4edda; color:#155724; border-radius:5px; padding:4px;} "
                "QPushButton:hover {background-color:#28a745; color:white;}"
            )
            btnApprove.clicked.connect(
                functools.partial(self.approve_student, student["user_id"])
            )

            # Reject button
            btnReject = QPushButton("Reject")
            btnReject.setMinimumWidth(70)
            btnReject.setMinimumHeight(30)
            btnReject.setStyleSheet(
                "QPushButton {background-color:#f8d7da; color:#721c24; border-radius:5px; padding:4px;} "
                "QPushButton:hover {background-color:#c82333; color:white;}"
            )
            btnReject.clicked.connect(
                functools.partial(self.reject_student, student["user_id"])
            )

            # Buttons inside same cell
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            layout.addWidget(btnApprove)
            layout.addWidget(btnReject)
            table.setCellWidget(row_idx, 7, container)

            # Checkbox for bulk processing
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            table.setItem(row_idx, 0, chk_item)

    # ----------------------------------------------------------------------
    # TABLE FORMATTING
    # ----------------------------------------------------------------------
    def format_table(self):
        table = self.ui.tableRequests
        headers = ["S", "#", "Student ID", "Name", "Email", "Program", "State", "Actions"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()

        # Fixed size for checkbox column
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 60)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 200)
        table.setColumnWidth(4, 260)

        # Other columns can resize
        for col in range(5, len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        
        table.setSortingEnabled(True)
        table.verticalHeader().setDefaultSectionSize(100)

    # ----------------------------------------------------------------------
    # SEARCH BAR
    # ----------------------------------------------------------------------
    def search_students(self):
        text = self.ui.lineEditSearch.text().lower()

        filtered = [
            s for s in self.students_data
            if text in s["name"].lower() or text in str(s["user_id"])
        ]

        self.fill_table(filtered)

    # ----------------------------------------------------------------------
    # INDIVIDUAL APPROVE / REJECT
    # ----------------------------------------------------------------------
    def approve_student(self, user_id):
        """
        Approves a single student and sends email.
        """
        reply = self.blf.show_confirmation(
            "Approve Student",
            f"Are you sure you want to approve student ID {user_id}?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        name, email = self.get_user_name_email(user_id)
        msg = self.admin.admin_approve_student(user_id)

        self.send_approval_email(name, email, user_id)

        print("[ADMIN]", msg)
        self.load_pending_students()

    def reject_student(self, user_id):
        """
        Rejects a single student and sends email.
        """
        reply = self.blf.show_confirmation(
            "Reject Student",
            f"Are you sure you want to reject student ID {user_id}?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        name, email = self.get_user_name_email(user_id)
        msg = self.admin.admin_reject_student(user_id)

        self.send_rejection_email(name, email)

        print("[ADMIN]", msg)
        self.load_pending_students()

    # ----------------------------------------------------------------------
    # BULK APPROVE / REJECT
    # ----------------------------------------------------------------------
    def get_selected_user_ids(self):
        """
        Returns IDs of all selected rows via checkbox.
        """
        table = self.ui.tableRequests
        ids = []

        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                ids.append(int(table.item(row, 2).text()))

        return ids

    def approve_selected_students(self):
        selected_ids = self.get_selected_user_ids()

        # Case 1: No selection, approve ALL students shown
        if not selected_ids:
            reply = self.blf.show_confirmation(
                "Approve All Students",
                "Approve all pending students?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            for s in self.students_data:
                self.send_approval_email(s["name"], s["email"], s["user_id"])

            msg = self.admin.admin_approve_all_pending_students()
            print("[ADMIN]", msg)
            self.load_pending_students()
            return

        # Case 2: Approve selected students only
        reply = self.blf.show_confirmation(
            "Approve Selected Students",
            f"Approve {len(selected_ids)} selected student(s)?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for uid in selected_ids:
            name, email = self.get_user_name_email(uid)
            self.admin.admin_approve_student(uid)
            self.send_approval_email(name, email, uid)

        self.load_pending_students()

    def reject_selected_students(self):
        selected_ids = self.get_selected_user_ids()

        # Case 1: Reject all if none selected
        if not selected_ids:
            reply = self.blf.show_confirmation(
                "Reject All Students",
                "Reject all pending students?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            for s in self.students_data:
                self.send_rejection_email(s["name"], s["email"])

            msg = self.admin.admin_reject_all_pending_students()
            print("[ADMIN]", msg)
            self.load_pending_students()
            return

        # Case 2: Reject selected only
        reply = self.blf.show_confirmation(
            "Reject Selected Students",
            f"Reject {len(selected_ids)} selected student(s)?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for uid in selected_ids:
            name, email = self.get_user_name_email(uid)
            self.admin.admin_reject_student(uid)
            self.send_rejection_email(name, email)

        self.load_pending_students()

    # ----------------------------------------------------------------------
    # EMAIL HELPERS
    # ----------------------------------------------------------------------
    def get_user_name_email(self, user_id):
        """
        Returns (name, email) for a user based on cached students_data.
        """
        for s in self.students_data:
            if s["user_id"] == user_id:
                return s["name"], s["email"]
        return None, None

    def send_approval_email(self, name, email, user_id):
        """
        Sends approval email containing name and ID.
        """
        if email is None:
            return

        subject = "Account Approved"
        body = (
            f"Hello {name},\n\n"
            f"Congratulations! Your ECE-REGISTRATION-SYSTEM account has been approved.\n"
            f"Your ID is: {user_id}\n\n"
            f"You may now log in and use all services.\n\n"
            f"Regards,\n-ECE-Lions Administration."
        )
        self.es.send_email(email, subject, body)

    def send_rejection_email(self, name, email):
        """
        Sends rejection email to unapproved.
        """
        if email is None:
            return

        subject = "Account Rejected"
        body = (
            f"Hello {name},\n\n"
            f"Unfortunately, Your ECE-REGISTRATION-SYSTEM account request has been rejected.\n"
            f"If you believe this is an error, you may contact support.\n\n"
            f"Regards,\n-ECE-Lions Administration."
        )
        self.es.send_email(email, subject, body)

    # ----------------------------------------------------------------------
    # BUTTON STATE CONTROL
    # ----------------------------------------------------------------------
    def update_approve_reject_button_state(self):
        """
        Updates text and enabled state of the Approve/Reject buttons based on
        how many checkboxes are selected.
        """
        table = self.ui.tableRequests
        selected_count = 0

        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected_count += 1

        if selected_count > 0:
            self.ui.btnApproveAll.setText(f"Approve Selected ({selected_count})")
            self.ui.btnApproveAll.setEnabled(True)
            self.ui.btnRejectAll.setText(f"Reject Selected ({selected_count})")
            self.ui.btnRejectAll.setEnabled(True)
        else:
            self.ui.btnApproveAll.setText("Approve All")
            self.ui.btnApproveAll.setEnabled(bool(self.students_data))
            self.ui.btnRejectAll.setText("Reject All")
            self.ui.btnRejectAll.setEnabled(bool(self.students_data))

    # ----------------------------------------------------------------------
    # UPDATE COUNTER LABEL
    # ----------------------------------------------------------------------
    def update_pending_counter(self):
        self.ui.labelPendingCount.setText(f"Total Pending: {len(self.students_data)}")


# ----------------------------------------------------------------------
# STANDALONE TEST
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = QWidget()
    ui = Ui_PendingRequestsWidget()
    ui.setupUi(window)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    controller = PendingRequestsController(ui, admin_utils)

    window.show()
    sys.exit(app.exec())
