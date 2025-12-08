import sys, os
from PyQt6 import QtWidgets

# Setup path to reach project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.admin_ui.submenus_ui.ui_course_prereq_dialog import Ui_CoursePrereqDialog
from helper_files.shared_utilities import warning, error, info


class CoursePrereqDialogController:

    def __init__(self, dialog: QtWidgets.QDialog, admin_utils):
        self.dialog = dialog
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        self.ui = Ui_CoursePrereqDialog()
        self.ui.setupUi(dialog)

        self.selected_course = None

        # Disable buttons until a course is selected
        self.ui.buttonAdd.setEnabled(False)
        self.ui.buttonRemove.setEnabled(False)

        self.populate_courses()
        self.connect_signals()

    # ----------------- POPULATE COURSES -----------------
    def populate_courses(self):
        self.ui.comboBoxSelectCourse.clear()
        self.ui.comboBoxSelectCourse.addItem("Select a course...", None)
        
        # admin.list_courses() returns tuples (code, name, credits)
        courses = self.admin_utils.list_courses() or []
        for code, name, *_ in courses:
            clean_code = str(code).strip()
            self.ui.comboBoxSelectCourse.addItem(f"{clean_code} - {name}", clean_code)

    # ----------------- CONNECT SIGNALS -----------------
    def connect_signals(self):
        self.ui.comboBoxSelectCourse.currentIndexChanged[int].connect(self.on_course_selected)
        self.ui.buttonAdd.clicked.connect(self.on_add_prereq)
        self.ui.buttonRemove.clicked.connect(self.on_remove_prereq)
        self.ui.buttonClose.clicked.connect(self.dialog.close)

    # ----------------- COURSE SELECTION -----------------
    def on_course_selected(self, index: int):
        try:
            if index <= 0:
                self.selected_course = None
                self.clear_lists()
                return

            code = self.ui.comboBoxSelectCourse.itemData(index)
            if not code:
                self.selected_course = None
                self.clear_lists()
                return

            self.selected_course = str(code).strip()
            self.ui.buttonAdd.setEnabled(True)
            self.ui.buttonRemove.setEnabled(True)
            self.refresh_prereqs()
        except Exception as e:
            error(self.dialog, f"Unexpected error: {e}")

    # ----------------- CLEAR LISTS -----------------
    def clear_lists(self):
        self.ui.listWidgetCurrentPrereq.clear()
        self.ui.listWidgetAddPrereq.clear()
        self.ui.buttonAdd.setEnabled(False)
        self.ui.buttonRemove.setEnabled(False)

    # ----------------- REFRESH PREREQUISITES -----------------
    def refresh_prereqs(self):
        self.ui.listWidgetCurrentPrereq.clear()
        self.ui.listWidgetAddPrereq.clear()
        
        if not self.selected_course:
            return 

        try:
            # 1. Create a Lookup Map for Course Names { 'MATH101': 'Calculus I' }
            all_courses = self.admin_utils.list_courses() or []
            course_map = {str(c[0]).strip(): str(c[1]).strip() for c in all_courses}

            # 2. Get prerequisites (Now returns full codes like 'MATH101' due to Fix #1)
            prereq_codes = [str(p).strip() for p in self.admin_utils.list_prerequisites(self.selected_course)]
            
            # 3. Populate "Current Prerequisites" with Name lookup
            current_display_items = []
            for code in prereq_codes:
                name = course_map.get(code, "Unknown Name")
                current_display_items.append(f"{code} - {name}")
            
            self.ui.listWidgetCurrentPrereq.addItems(current_display_items)

            # 4. Populate "Add Prerequisites" (Filter out existing ones)
            to_add_display_items = []
            for c in all_courses:
                c_code = str(c[0]).strip()
                c_name = str(c[1]).strip()
                
                if c_code != self.selected_course and c_code not in prereq_codes:
                    to_add_display_items.append(f"{c_code} - {c_name}")
            
            self.ui.listWidgetAddPrereq.addItems(to_add_display_items)

        except Exception as e:
            print(f"Debug Error: {e}") # Print error to console for debugging
            error(self.dialog, f"Failed to refresh prerequisites: {e}")

    # ----------------- ADD PREREQUISITE -----------------
    def on_add_prereq(self):
        if not self.selected_course:
            return

        selected_items = self.ui.listWidgetAddPrereq.selectedItems()
        if not selected_items:
            warning(self.dialog, "Select prerequisites to add.")
            return
        
        for item in selected_items:
            # Extract "MATH101" from "MATH101 - Calculus"
            full_text = item.text()
            code = full_text.split(" - ")[0].strip()
            
            # Add to DB
            self.admin_utils.add_prerequisites(self.selected_course, [code])
        
        self.refresh_prereqs()


    # ----------------- REMOVE PREREQUISITE -----------------
    def on_remove_prereq(self):
        if not self.selected_course:
            return

        selected_items = self.ui.listWidgetCurrentPrereq.selectedItems()
        if not selected_items:
            warning(self.dialog, "Select prerequisites to remove.")
            return

        for item in selected_items:
            # Extract "MATH101" from "MATH101 - Calculus"
            full_text = item.text()
            code_to_remove = full_text.split(" - ")[0].strip()
            
            # Remove from DB
            self.admin_utils.delete_prerequisite(self.selected_course, code_to_remove)

        self.refresh_prereqs()
        


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    controller = CoursePrereqDialogController(dialog, admin_utils)
    dialog.show()
    sys.exit(app.exec())