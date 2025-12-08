import os, sys
# Ensure path is set correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt6.QtCore import Qt

# Import the AdminUtilities instance (assuming it's named 'admin' in its file)
from admin.submenus.class_course_prereq_dialog import CoursePrereqDialogController

from app_ui.admin_ui.submenus_ui.ui_manage_prereq import Ui_ManagePrereqs
from helper_files.shared_utilities import BaseLoginForm


class ManagePrerequisitesController:

    # NOTE: We now take the AdminUtilities instance (admin) to access list_prerequisites
    def __init__(self, ui, admin_utils):
        self.ui = ui
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        self.courses_data = []
        self.blf = BaseLoginForm() # Used for the animation utility

        self.connect_ui_signals()
        self.load_courses()
        self.format_table()

    # ------------------ SIGNALS ------------------
    def connect_ui_signals(self):
        self.ui.lineEditSearch.textChanged.connect(self.search_courses)
        self.ui.buttonRefresh.clicked.connect(self.handle_refresh)
        # We need to refresh the table after the dialog is closed
        self.ui.buttonManagePrereq.clicked.connect(self.handle_manage_prereq)

    # ------------------ REFRESH ------------------
    def handle_refresh(self):
        # Use the BaseLoginForm utility for animation (if available)
        if hasattr(BaseLoginForm, 'animate_label_with_dots'):
            BaseLoginForm.animate_label_with_dots(
                self.ui.labelTotalCoursesCount,
                base_text="Refreshing",
                interval=400,
                duration=2000,
                on_finished=self.load_courses
            )
        else:
            self.load_courses()

    # ------------------ LOAD COURSES (FIXED) ------------------
    def load_courses(self):
        self.courses_data.clear()
        self.ui.tableAllCourses.setRowCount(0)

        # FIX: Use the admin instance (self.admin) to get the course list.
        # This instance is responsible for looking up the prerequisites for display.
        rows = self.db.ListCourses() # This should return (code, name, credits)

        for i, row in enumerate(rows, start=1):
            course_code = str(row[0]).strip()
            
            # Fetch prerequisites using the admin utility for the current course
            prereq_codes = self.db.list_prerequisites(course_code)
            
            # Convert the list of codes into a readable string
            prereq_str = ", ".join(prereq_codes)

            course = {
                "row_number": i,
                "code": course_code,
                "name": str(row[1]),
                # The full, comma-separated string of prerequisites
                "prereq": prereq_str 
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
            item_number.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row_idx, 0, item_number)

            # Course Code & Name
            table.setItem(row_idx, 1, QTableWidgetItem(course["code"]))
            table.setItem(row_idx, 2, QTableWidgetItem(course["name"]))

            # Prerequisites column (Now uses the calculated string)
            table.setItem(row_idx, 3, QTableWidgetItem(course["prereq"]))
            
            # Center alignment for the first column
            item_number.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    # ------------------ FORMAT TABLE ------------------
    def format_table(self):
        table = self.ui.tableAllCourses
        headers = ["#", "COURSE CODE", "COURSE NAME", "PREREQ"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setDefaultSectionSize(60)

        table.setColumnWidth(0, 50)
        table.setColumnWidth(1, 140)
        table.setColumnWidth(2, 240)
        table.setColumnWidth(3, 200)

    # ------------------ SEARCH ------------------
    def search_courses(self):
        text = self.ui.lineEditSearch.text().lower()
        filtered = [
            c for c in self.courses_data
            if text in c["code"].lower() or text in c["name"].lower() or text in c["prereq"].lower()
        ]
        self.fill_table(filtered)

    # ------------------ MANAGE PREREQUISITES ------------------
    def handle_manage_prereq(self):
        dialog = QtWidgets.QDialog()
        
        # Instantiate the controller, passing the dialog instance
        controller = CoursePrereqDialogController(dialog, self.admin_utils)

        # Show the dialog modally
        dialog.exec()
        
        # FIX: Refresh the course list and table after the dialog is closed 
        # (This updates the 'PREREQ' column with the new prerequisites)
        self.load_courses()

    # ------------------ TOTAL COUNTER ------------------
    def update_total_counter(self):
        self.ui.labelTotalCoursesCount.setText(
            f"Total Courses: {len(self.courses_data)}"
        )


# ---------------- MAIN APP ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)


    # If the file naming convention means 'admin' is the instance, we use it directly.

    window = QWidget()
    ui = Ui_ManagePrereqs()
    ui.setupUi(window)

    from database_files.class_database_uitlities import DatabaseUtilities
    from database_files.cloud_database import get_pooled_connection
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    controller = ManagePrerequisitesController(ui, admin_utils)

    window.show()
    sys.exit(app.exec())