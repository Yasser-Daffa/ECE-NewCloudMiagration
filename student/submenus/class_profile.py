# class_profile_widget.py

import os
import sys

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

# Student Profile UI
from app_ui.student_ui.submenus_ui.ui_profile import Ui_Profile

# Message helpers + email validation
from helper_files.shared_utilities import info, warning, error
from helper_files.validators import validate_email

# Student database object
from student.class_student_utilities import db


class ProfileWidget(QWidget):
    """
    Student Profile Widget:
    - Loads the student Ui_Profile layout
    - Displays student data (name, email, program, department is fixed)
    - Allows editing email only (name stays read-only)
    - Activates the 'Edit Email' button only if the email changes
    - Updates the email inside the database using update_user()
    """

    def __init__(self, student_user_data, parent=None):
        """
        student_user_data → (user_id, name, email, program, state, account_status)
        """
        super().__init__(parent)

        # ----------------- Setup UI -----------------
        self.ui = Ui_Profile()
        self.ui.setupUi(self)

        # ----------------- Store DB and user info -----------------
        self.db = db
        self.student_id = student_user_data[0]
        self.name = student_user_data[1] or ""
        self.email = student_user_data[2] or ""
        self.program = student_user_data[3] or ""   # Example: COMP, PWM, etc.

        # Store original email to track changes
        self._original_email = self.email

        # ----------------- Load data into UI -----------------
        self.load_initial_data()

        # These fields must not be editable
        self.ui.lineEditName.setReadOnly(True)
        # If UI includes these:
        # self.ui.lineEditProgram.setReadOnly(True)
        # self.ui.lineEditDepartment.setReadOnly(True)

        # ----------------- Connect buttons -----------------
        # 'Edit Email' acts as the save button
        self.ui.buttonEditEmail.clicked.connect(self.save_changes)


        # ----------------- Track changes -----------------
        # Only email can change, so only track that field
        self.ui.lineEditEmail.textChanged.connect(self.on_fields_changed)

        # Initially, nothing changed → disable save button
        self.set_dirty(False)

    # ---------------------------------------------------------
    # INITIAL DATA
    # ---------------------------------------------------------
    def load_initial_data(self):
        """Places student data into the UI fields."""
        self.ui.lineEditName.setText(self.name)
        self.ui.lineEditEmail.setText(self.email)

        # If additional student fields exist in UI, fill them
        if hasattr(self.ui, "lineEditProgram"):
            self.ui.lineEditProgram.setText(self.program or "N/A")

        if hasattr(self.ui, "lineEditDepartment"):
            self.ui.lineEditDepartment.setText("Electrical and Computer Engineering")

    # ---------------------------------------------------------
    # DIRTY STATE (detects if there are unsaved changes)
    # ---------------------------------------------------------
    def set_dirty(self, dirty: bool):
        """
        dirty = True  → enable Edit Email button
        dirty = False → disable Edit Email button
        """
        self.ui.buttonEditEmail.setEnabled(dirty)

    def on_fields_changed(self):
        """
        Triggered whenever the email field changes.
        If the current email differs from the original email → enable save button.
        """
        current_email = self.ui.lineEditEmail.text().strip()
        dirty = (current_email != self._original_email)
        self.set_dirty(dirty)

    # ---------------------------------------------------------
    # SAVE CHANGES (email only) with safety try/except
    # ---------------------------------------------------------
    def save_changes(self):
        new_email = self.ui.lineEditEmail.text().strip()

        # Ensure email is not empty
        if not new_email:
            warning(self, "Email cannot be empty.")
            return

        # Validate the email format
        email_error = validate_email(new_email)
        if email_error:
            warning(self, "Invalid Email")
            return

        # If nothing changed
        if new_email == self._original_email:
            warning(self, "No Changes")
            self.set_dirty(False)
            return

        # Try updating the email (safe block)
        try:
            result = self.db.update_user(
                self.student_id,
                email=new_email
            )
        except Exception as e:
            # In case of unexpected errors (database connection, etc.)
            error(self, f"Unexpected error while updating email: {e}")
            return

        # If DB returned a success message
        if isinstance(result, str) and "successfully" in result.lower():
            info(self, "Profile updated successfully.")

            # Update internal values so the UI reflects the new state
            self.email = new_email
            self._original_email = new_email

            self.set_dirty(False)
        else:
            # If database returned an error message (e.g., duplicate email)
            if isinstance(result, str):
                error(self, result)
            else:
                error(self, "Error updating profile.")

    # ---------------------------------------------------------
    # CANCEL EDIT
    # ---------------------------------------------------------
    def cancel_edit(self):
        """
        Restores email to the original value and disables the save button.
        Name is always read-only, so only the email is reverted.
        """
        self.ui.lineEditEmail.setText(self._original_email)
        self.set_dirty(False)