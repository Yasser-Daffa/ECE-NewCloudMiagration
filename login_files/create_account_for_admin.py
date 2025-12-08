import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
)
from PyQt6.QtCore import QTimer

# -----------------------------
# UI Pages
# -----------------------------
from login_files.ui_files.class_create_admin_account_widget import CreateAdminAccountWidget
from login_files.ui_files.class_confirm_email_widget import ConfirmEmailWidget

# -----------------------------
# Shared helpers and utilities
# -----------------------------
from helper_files.shared_utilities import BaseLoginForm, EmailSender, CodeGenerator
from helper_files.validators import (
    hash_password,
    validate_full_name,
    validate_email,
)

# -----------------------------
# Database connection
# -----------------------------


class SignupAndConfirmWindow(BaseLoginForm):
    """
    Standalone admin-registration window. Handles:
    - Displaying CreateAccountWidget
    - Sending verification email
    - Displaying ConfirmEmailWidget
    - Validating code
    - Creating admin accounts in the DB

    No login page, no reset-password flow.
    Only creates ADMIN accounts.
    """

    def __init__(self, admin_utils, parent: QWidget | None = None):
        super().__init__(parent)

        # Persistent resources
        self.admin_utils = admin_utils
        self.db = admin_utils.db
        self.email_sender = EmailSender()

        # Temporary storage for account creation
        self.new_user_data: dict = {}

        # Maps each email → CodeGenerator
        self.code_generators: dict[str, CodeGenerator] = {}

        # -----------------------------
        # Create UI pages
        # -----------------------------
        self.create_account_page = CreateAdminAccountWidget()
        self.confirm_email_page = ConfirmEmailWidget()

        # -----------------------------
        # Stacked widget setup
        # -----------------------------
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.create_account_page)  # index 0
        self.stacked.addWidget(self.confirm_email_page)   # index 1
        self.stacked.setCurrentIndex(0)

        # -----------------------------
        # Main layout
        # -----------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)

        # Initial page and UI adjustments
        self.go_to_create_account()
        self.create_account_page.labelGeneralStatus.setText("")

        # -----------------------------
        # Signal connections
        # -----------------------------
        self.create_account_page.buttonCreateAccont.clicked.connect(
            self.handle_create_account_click
        )


        self.confirm_email_page.buttonBackToCreateAccount.clicked.connect(
            self.handle_back_to_create_account
        )
        self.confirm_email_page.buttonBackToSignIn.clicked.connect(
            self.handle_back_to_sign_in
        )
        self.confirm_email_page.buttonVerifyCode.clicked.connect(
            self.handle_email_confirmation
        )
        self.confirm_email_page.buttonReSendCode.clicked.connect(self.resend_code)

        # Window configuration
        self.resize(900, 600)
        self.setWindowTitle("Admin Sign Up & Email Verification")

    # =========================================================
    # NAVIGATION
    # =========================================================
    def go_to_create_account(self):
        """Switch to account creation page."""
        self.stacked.setCurrentIndex(0)

    def go_to_confirm_email(self):
        """Switch to email confirmation page."""
        self.confirm_email_page.lineEditVerificationCode.clear()
        self.stacked.setCurrentIndex(1)

    # =========================================================
    # CREATE ACCOUNT → VALIDATE → SEND CODE
    # =========================================================
    def handle_create_account_click(self):
        """Triggered when user clicks 'Create Account'."""

        raw_full_name = self.create_account_page.fullName.text().strip()
        raw_email = self.create_account_page.email.text().strip()
        raw_password = self.create_account_page.password.text()

        labelStatus = self.create_account_page.labelGeneralStatus

        # Validate full name
        parts, err = validate_full_name(raw_full_name)
        if err:
            labelStatus.setText(err)
            self.set_label_color(labelStatus, "red")
            return
        full_name = " ".join(parts)

        # Validate email
        err = validate_email(raw_email)
        if err:
            labelStatus.setText(err)
            self.set_label_color(labelStatus, "red")
            return

        # Ensure email does not already exist
        if self.db.check_email_exists(raw_email):
            self.create_account_page.highlight_invalid_lineedit(
                self.create_account_page.email,
                "Email already exists.",
            )
            labelStatus.setText("Email already registered.")
            self.set_label_color(labelStatus, "red")
            return

        # Store user data until confirmation
        self.new_user_data = {
            "name": full_name,
            "email": raw_email,
            "password": raw_password,
            "program": None,    # Admin has no program
            "state": "admin",
        }

        labelStatus.setText("All good! Please confirm your email...")
        self.set_label_color(labelStatus, "green")

        # Create or reuse a CodeGenerator
        if raw_email not in self.code_generators:
            self.code_generators[raw_email] = CodeGenerator(validity_minutes=5)

        # Send verification code
        sent = self.send_verification_code(raw_email)
        if sent:
            print(f"Verification code sent: {self.code_generators[raw_email].code}")

        # Move to confirm page shortly after
        QTimer.singleShot(1500, self.go_to_confirm_email)

    def send_verification_code(self, to_email: str) -> bool:
        """Create or refresh verification code and send it to the user."""

        if to_email not in self.code_generators:
            self.code_generators[to_email] = CodeGenerator(validity_minutes=5)

        generator = self.code_generators[to_email]
        code = generator.generate_verification_code()

        subject = "Your Verification Code"
        body = (
            f"Your verification code is: {code}\n"
            f"Expires in {generator.validity_minutes} minutes."
        )

        sent = self.email_sender.send_email(to_email, subject, body)

        if sent:
            QMessageBox.information(self, "Code Sent", "A verification code was sent to your email.")
            self.confirm_email_page.start_cooldown_timer()
        else:
            QMessageBox.critical(self, "Error", "Failed to send verification email.")

        return sent

    # =========================================================
    # CONFIRMATION LOGIC
    # =========================================================
    def check_is_code_valid(self, entered_code: str, email: str) -> tuple[bool, str]:
        """Return (valid, reason) after evaluating the entered code."""

        if not entered_code:
            return False, "Code cannot be empty."

        generator = self.code_generators.get(email)
        if not generator:
            return False, "No code generated for this email."

        if entered_code != generator.code:
            return False, "Incorrect verification code."

        if generator.is_code_expired():
            return False, "The code has expired. Please request a new one."

        return True, ""

    def handle_email_confirmation(self):
        """Triggered when user clicks 'Verify Code'."""

        if not self.new_user_data:
            QMessageBox.warning(self, "Error", "No registration data found.")
            return

        entered_code = self.confirm_email_page.lineEditVerificationCode.text().strip()
        email = self.new_user_data["email"]

        is_valid, reason = self.check_is_code_valid(entered_code, email)
        if not is_valid:
            self.shake_widget(self.confirm_email_page.lineEditVerificationCode)
            self.highlight_invalid_lineedit(
                self.confirm_email_page.lineEditVerificationCode,
                reason,
            )
            if reason != "Code cannot be empty.":
                QMessageBox.warning(self, "Invalid Code", reason)
            return

        # Verification OK → create account
        QMessageBox.information(self, "Code Verified", "Email verified successfully!")

        hashed_pw = hash_password(self.new_user_data["password"])
        result = self.db.add_users(
            self.new_user_data["name"],
            self.new_user_data["email"],
            hashed_pw,
            self.new_user_data["program"], # always none for admin
            self.new_user_data["state"],   # "admin"
                                           # Status Always active for admins
        )

        if "successfully" in result:
            QMessageBox.information(
                self,
                "Email Confirmed",
                "Admin account created successfully.",
            )
            QTimer.singleShot(1000, self.close)
        else:
            QMessageBox.critical(self, "Error", f"An error occurred: {result}")

    # =========================================================
    # RESEND CODE
    # =========================================================
    def resend_code(self):
        if not self.new_user_data:
            QMessageBox.warning(self, "Error", "No registration data found.")
            return

        email = self.new_user_data["email"]
        if self.send_verification_code(email):
            QMessageBox.information(self, "Code Sent", "Verification code resent successfully.")

    # =========================================================
    # BACK NAVIGATION
    # =========================================================
    def handle_back_to_create_account(self):
        """Return to page 0 with warning."""
        response = self.show_confirmation(
            "Are you sure?",
            "Going back might cancel the registration process.",
        )
        if response == QMessageBox.StandardButton.Yes:
            self.go_to_create_account()

    def handle_back_to_sign_in(self):
        """Close the dialog entirely."""
        response = self.show_confirmation(
            "Are you sure?",
            "Going back will close the registration window.",
        )
        if response == QMessageBox.StandardButton.Yes:
            self.close()


# -------------------------------------------------------------
# Standalone Test
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)
    admin_utils = AdminUtilities(db)

    window = SignupAndConfirmWindow(admin_utils)
    window.show()
    sys.exit(app.exec())
