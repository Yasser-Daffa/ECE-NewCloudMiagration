# class_profile_widget.py

import os
import sys

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from app_ui.admin_ui.submenus_ui.ui_profile import Ui_Profile
from helper_files.shared_utilities import info, warning, error
from helper_files.validators import validate_email


class ProfileWidget(QWidget):
    """
    Simple Profile Widget:
    - Loads Ui_Profile
    - Displays admin data (name, email, department is fixed)
    - Allows editing email only (name is read-only)
    - Enables Save only when email is changed
    - Updates email in the database using update_user()
    """

    def __init__(self, admin_utils, admin_user_data, parent=None):
        """
        admin_user_data -> (user_id, name, email, program, state, account_status)
        """
        super().__init__(parent)

        self.ui = Ui_Profile()
        self.ui.setupUi(self)

        # Store utilities
        self.admin_utils = admin_utils
        self.db = admin_utils.db

        # ----------------- Store DB and user info -----------------
        self.admin_id = admin_user_data[0]
        self.name = admin_user_data[1]
        self.email = admin_user_data[2]
        self.program = admin_user_data[3]   # Currently unused, but kept for future use

        # Store original values for change detection
        self._original_name = self.name
        self._original_email = self.email

        # ----------------- Load data into UI -----------------
        self.load_initial_data()

        # Name is read-only
        self.ui.lineEditName.setReadOnly(True)
        # To disable it visually as well:
        # self.ui.lineEditName.setEnabled(False)

        # ----------------- Connect buttons -----------------
        self.ui.buttonEditEmail.clicked.connect(self.save_changes)


        # ----------------- Track changes in fields -----------------
        # Only email is editable, so only track email field
        self.ui.lineEditEmail.textChanged.connect(self.on_fields_changed)

        # At start, no changes → disable Save
        self.set_dirty(False)

    # ---------------------------------------------------------
    # INITIAL DATA
    # ---------------------------------------------------------
    def load_initial_data(self):
        """Places admin data in the UI fields."""
        self.ui.lineEditName.setText(self.name)
        self.ui.lineEditEmail.setText(self.email)

        # Static/fixed department label
        self.ui.lineEditDepartment.setText("Electrical and Computer Engineering")

    # ---------------------------------------------------------
    # DIRTY STATE (tracks whether there are unsaved changes)
    # ---------------------------------------------------------
    def set_dirty(self, dirty: bool):
        """
        dirty = True  -> enable Save
        dirty = False -> disable Save
        """
        self.ui.buttonEditEmail.setEnabled(dirty)

    def on_fields_changed(self):
        """
        Triggered automatically whenever the email field changes.
        If new email =! old email -> enable Save.
        """
        current_email = self.ui.lineEditEmail.text().strip()
        dirty = (current_email != self._original_email)
        self.set_dirty(dirty)

    # ---------------------------------------------------------
    # SAVE CHANGES (email only)
    # ---------------------------------------------------------
    def save_changes(self):
        """Validates and updates email."""
        new_email = self.ui.lineEditEmail.text().strip()

        # Email cannot be empty
        if not new_email:
            warning(self, "Email cannot be empty.")
            return

        # Validate email format
        email_error = validate_email(new_email)
        if email_error:
            warning(self, "Invalid Email")
            return

        # Only update if email has changed
        email_to_update = new_email if new_email != self._original_email else None

        if email_to_update is None:
            warning(self, "No Changes")
            return

        # ---------- هنا حطينا try / except على دالة الداتابيس ----------
        try:
            result = self.db.update_user(
                self.admin_id,
                email=email_to_update
            )
        except Exception as e:
            # لو صار أي خطأ غير متوقع من الداتابيس
            error(self, f"Error updating profile: {e}")
            return
        # -----------------------------------------------------------

        # نتحقق من نتيجة الدالة (لو رجعت نص فيه successfully)
        if isinstance(result, str) and "successfully" in result.lower():
            info(self, "Profile updated successfully.")

            # Update stored internal values
            self.email = email_to_update
            self._original_email = email_to_update

            # Disable Save again
            self.set_dirty(False)
        else:
            # لو رجعت رسالة خطأ من الدالة نفسها
            if isinstance(result, str):
                error(self, result)
            else:
                error(self, "Error")

    # ---------------------------------------------------------
    # CANCEL EDIT
    # ---------------------------------------------------------
    def cancel_edit(self):
        """
        Restores the email field back to original value.
        Name is fixed and does not change.
        """
        self.ui.lineEditEmail.setText(self._original_email)
        self.set_dirty(False)
