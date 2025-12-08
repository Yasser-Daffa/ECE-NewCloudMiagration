import os, sys, functools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

# Add Course dialog UI (generated from Qt Designer)
from app_ui.admin_ui.submenus_ui.ui_add_courses_dialog import Ui_AddCourseDialog

# Shared utilities class that provides shake effect, red border, and validation helpers
from helper_files.shared_utilities import BaseLoginForm

# Use the ready-made admin instance from class_admin_utilities


class AddCoursesDialog(QDialog, BaseLoginForm):
    """
    Dialog responsible for:
    - Reading input fields from the UI
    - Validating the input data
    - Using shake effect and visual feedback for invalid fields
    - Calling add_course in the admin utilities layer
    """

    def __init__(self, admin_utils, parent=None):
        # Explicitly initialize both QDialog and BaseLoginForm parents
        QDialog.__init__(self, parent)
        BaseLoginForm.__init__(self, parent)

        self.ui = Ui_AddCourseDialog()
        self.ui.setupUi(self)

        # admin_utils is expected to be an object that exposes add_course
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        # Initially disable the Save button until required fields are valid
        self.ui.buttonSave.setEnabled(False)

        # Connect dialog buttons (Save and Cancel)
        self.ui.buttonSave.clicked.connect(self.on_save_clicked)
        self.ui.buttonCancel.clicked.connect(self.reject)

        # Attach "non-empty" validators to required line edits (from BaseLoginForm helper methods)
        self.attach_non_empty_validator(self.ui.lineEditCourseCode, "Course code")
        self.attach_non_empty_validator(self.ui.lineEditCourseName, "Course name")
        # Note: credits are taken from a spin box, which already guarantees a numeric value

        # Whenever any field changes, re-check if all required fields are filled
        self.ui.lineEditCourseCode.textChanged.connect(self.check_all_fields_filled)
        self.ui.lineEditCourseName.textChanged.connect(self.check_all_fields_filled)
        self.ui.spinBoxCreditHours.textChanged.connect(self.check_all_fields_filled)

        # Initial check to set the correct state of the Save button
        self.check_all_fields_filled()

    # ------------------------ Enable/Disable Save Button ------------------------
    def check_all_fields_filled(self):
        """
        Check if all required fields have values.
        If they do, enable the Save button; otherwise, keep it disabled.
        """
        code = self.ui.lineEditCourseCode.text().strip()
        name = self.ui.lineEditCourseName.text().strip()
        credits = self.ui.spinBoxCreditHours.text().strip()

        # Save button is only enabled when all fields are non-empty
        if code and name and credits:
            self.ui.buttonSave.setEnabled(True)
        else:
            self.ui.buttonSave.setEnabled(False)

    # ------------------------ Message Boxes (Black Text, White Background) ------------------------

    def show_error(self, message: str):
        """Show an error message box with black text and white background."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("Error")
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Style to ensure the background is white and text is black
        box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: black;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 12pt;
            }
            QMessageBox QPushButton {
                color: black;
                padding: 6px 14px;
            }
            """)

        box.exec()

    def show_info(self, message: str):
        """Show a success/info message box with black text and white background."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Success")
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Same visual style as the error box for consistency
        box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: black;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 12pt;
            }
            QMessageBox QPushButton {
                color: black;
                padding: 6px 14px;
            }
        """)

        box.exec()

    # ------------------------ Save Button Handler ------------------------

    def on_save_clicked(self):
        """
        Handler for the Save button click:
        - Cleans and normalizes input
        - Validates required fields
        - Calls admin_utils.add_course
        - Handles duplicate course codes using visual feedback
        """
        code = self.ui.lineEditCourseCode.text().strip().upper()
        name = self.ui.lineEditCourseName.text().strip().title()
        credits_text = self.ui.spinBoxCreditHours.text().strip()

        # Extra safety: the button should already be disabled if fields are empty,
        # but we still guard against unexpected states.
        if not (code and name and credits_text):
            self.show_error("Please fill in all fields.")
            return

        # Reset any previous error border on the line edits before validating again
        self.reset_lineedit_border(self.ui.lineEditCourseCode)
        self.reset_lineedit_border(self.ui.lineEditCourseName)

        # Convert credit hours to integer (spin box ensures numeric input)
        credits = int(credits_text)

        # ===== If we reach this point, local validation passed =====
        msg = self.admin_utils.add_course(code, name, credits)

        # If the message indicates the course already exists, show validation feedback
        if msg.lower().startswith("course already"):
            # Highlight the course code field and show shake animation to draw attention
            self.highlight_invalid_lineedit(self.ui.lineEditCourseCode, msg)
            self.shake_widget(self.ui.lineEditCourseCode)
            self.show_error(msg)
            return

        # On success, show info message and close the dialog with accept()
        self.show_info(msg)
        


# =============================== MAIN ===============================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    dialog = AddCoursesDialog(admin_utils)
    dialog.show()

    sys.exit(app.exec())
