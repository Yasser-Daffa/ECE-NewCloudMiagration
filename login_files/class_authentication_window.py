import sys
import os

# Add project root to path (finalProject/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# -----------------------------
# UI + Page Classes
# -----------------------------
# from login_files.ui_files.ui_auth_stackedwidget import Ui_AuthStackedWidget
from login_files.ui_files.raw_ui.ui_auth_stackedwidget import Ui_AuthStackedWidget
from login_files.ui_files.class_login_widget import LoginWidget
from login_files.ui_files.class_create_account_widget import CreateAccountWidget
from login_files.ui_files.class_reset_password_widget import ResetPasswordWidget
from login_files.ui_files.class_confirm_email_widget import ConfirmEmailWidget
from login_files.ui_files.class_password_change_dialog import PasswordChangeDialog

# -----------------------------
# Shared base class and helpers
# -----------------------------
from helper_files.shared_utilities import (
    BaseLoginForm,
    EmailSender,
    CodeGenerator,
)
from helper_files.validators import (
    hash_password,
    validate_full_name,
    validate_email,
    validate_student_id
)

# -----------------------------
# Database utilities
# -----------------------------

from admin.class_admin_utilities import db



class AuthenticationWindow(BaseLoginForm, EmailSender): 
    def __init__(self):
        super().__init__()

        # Call it to create/connect the database and return the connection and cursor
        # This ensures all required tables, triggers, and constraints exist
        # con, cur = initialize_database("university_database.db")  # runs the table creation if missing

        # For logout button
        QApplication.instance().setQuitOnLastWindowClosed(True)
        
        # using the database we called from admin utils
        self.db = db
        # Email sender instance
        self.email_sender = EmailSender()

        # mode is none by default because we integrated a confirm email check in user profiles
        # it will be; mode = edit_profile for example
        self.mode = None
        self.profile_edit_email = None


        # --- 1. Load UI ---
        self.ui = Ui_AuthStackedWidget()
        self.ui.setupUi(self)

        # --- 2. Instantiate pages with DB ---
        self.login_page = LoginWidget()
        self.create_account_page = CreateAccountWidget()
        self.reset_password_page = ResetPasswordWidget()
        self.confirm_email_page = ConfirmEmailWidget()
        self.change_password_page = PasswordChangeDialog()

        # --- 3. Add pages to stacked widget ---
        self.ui.stackedWidgetAuth.addWidget(self.login_page)
        self.ui.stackedWidgetAuth.addWidget(self.create_account_page)
        self.ui.stackedWidgetAuth.addWidget(self.reset_password_page)
        self.ui.stackedWidgetAuth.addWidget(self.confirm_email_page)

        # --- 4. Set starting page ---
        self.ui.stackedWidgetAuth.setCurrentIndex(0)

        # --- 5. Connect navigation and action signals ---
        self.login_page.ui.buttonCreateAccount.clicked.connect(self.go_to_create_account)
        self.login_page.ui.buttonResetPassword.clicked.connect(self.go_to_reset_password)
        self.create_account_page.ui.buttonLoginHere.clicked.connect(self.go_to_login)
        self.create_account_page.ui.buttonCreateAccount.clicked.connect(self.handle_create_account_click)
        self.reset_password_page.ui.buttonBackToSignIn.clicked.connect(self.go_to_login)
        self.confirm_email_page.ui.buttonBackToCreateAccount.clicked.connect(self.handle_back_to_create_account)
        self.confirm_email_page.ui.buttonBackToSignIn.clicked.connect(self.handle_back_to_sign_in)
        self.confirm_email_page.ui.buttonVerifyCode.clicked.connect(self.handle_email_confirmation)

        # --- 6. disable general status labels initially ---
        self.login_page.ui.labelGeneralStatus.setText("")
        self.create_account_page.ui.labelGeneralStatus.setText("")
        

        # --- 7. Connect login action ---
        self.login_page.ui.buttonLogin.clicked.connect(self.handle_login)

        # --- 8. Connect email sending action ---
        self.confirm_email_page.ui.buttonReSendCode.clicked.connect(self.resend_code)

        # --- 9. Connect password reset actions ---
        self.login_page.ui.buttonResetPassword.clicked.connect(self.go_to_reset_password)
        self.reset_password_page.ui.buttonSendCode.clicked.connect(self.handle_password_reset_request)
        self.reset_password_page.ui.buttonVerifyCode.clicked.connect(self.handle_reset_code_confirmation)
        self.change_password_page.ui.buttonChangePassword.clicked.connect(self.update_password_from_dialog)

        # save codes
        self.code_generators = {}  # email -> CodeGenerator
        self.reset_code_generators = {}  # email -> CodeGenerator

    # =========================================================
    #                     NAVIGATION
    # =========================================================
    def go_to_login(self):
        self.new_user_data = {}  # clear any temp user data
        self.ui.stackedWidgetAuth.setCurrentIndex(0)

    def go_to_create_account(self):
        self.ui.stackedWidgetAuth.setCurrentIndex(1)

    def go_to_reset_password(self):
        """User clicked 'Reset Password' on login page."""
        self.reset_password_page.ui.lineEditRegisteredEmail.clear()
        self.reset_password_page.ui.lineEditCode.clear()
        self.ui.stackedWidgetAuth.setCurrentIndex(2)

    def go_to_confirm_email(self):
        self.confirm_email_page.ui.lineEditVerificationCode.clear()
        self.ui.stackedWidgetAuth.setCurrentIndex(3)


    def start_profile_edit_verification(self, email):
        """
        Activates the email verification mode used when editing the profile.
        Only verifies logged-in user's email, does NOT create accounts.
        """
        self.mode = "profile_edit"
        self.profile_edit_email = email

        # Clear inputs
        self.confirm_email_page.ui.lineEditVerificationCode.clear()

        # Generate & send a verification code
        self.code_generators[email] = CodeGenerator(validity_minutes=5)
        self.send_verification_code(email)

        # Jump directly to confirmation page
        self.ui.stackedWidgetAuth.setCurrentWidget(self.confirm_email_page)



    # =========================================================
    #                     LOGIN LOGIC
    # =========================================================
    def handle_login(self):
        # --- 1. Read input from login page ---
        login_input = self.login_page.ui.lineEditUsername.text().strip().lower()
        password = self.login_page.ui.lineEditPassword.text()
        self.labelStatus = self.login_page.ui.labelGeneralStatus

        # --- 2. Basic validation ---
        if not login_input or not password:
            self.labelStatus.setText("Please fill in all fields.")
            self.set_label_color(self.labelStatus, "red")
            return

        # --- 3. Validate input format ---
        # here we decide if login_input is email or student ID
        # and check input from user accordingly

        if login_input.isdigit():  # treat as student ID
            error = validate_student_id(login_input)
            if error:
                self.labelStatus.setText(error)
                self.set_label_color(self.labelStatus, "red")
                return
        else:  # treat as email
            error = validate_email(login_input)
            if error:
                self.labelStatus.setText(error)
                self.set_label_color(self.labelStatus, "red")
                return

        # --- 4. Fetch user from database ---
        user = self.db.get_user_by_login(login_input)
        if not user:
            self.labelStatus.setText("User not found.")
            self.set_label_color(self.labelStatus, "red")
            return

        user_id, name, email, program, state, account_status, hashed_pw = user

        # --- 5. Verify password ---
        from helper_files.validators import verify_password
        if not verify_password(password, hashed_pw):
            self.labelStatus.setText("Incorrect password.")
            self.set_label_color(self.labelStatus, "red")
            return

        # --- 6. Check account status ---
        if account_status != "active":
            self.labelStatus.setText(f"Account is {account_status}, cannot login yet.")
            self.set_label_color(self.labelStatus, "red")
            return

        # --- 7. Successful login ---
        self.labelStatus.setText("Login successful!")
        # Record last apperance for this user
        self.db.update_last_login(user_id)

        self.labelStatus.setStyleSheet("color: green;")
        print(f"Login successful for {name} ({state})")

        # --- 8. Redirect to the correct dashboard ---
        if state == "student":
            from student.class_student_dashboard import StudentDashboard
            from student.class_student_utilities import db 
            self.student_dash = StudentDashboard(db, user)
            self.student_dash.show()

        elif state == "admin":
            from admin.class_admin_dashboard import AdminDashboard
            from admin.class_admin_utilities import db
            self.admin_dash = AdminDashboard(db, user)
            self.admin_dash.show()



        # --- 9. Close authentication window ---
        self.close()


    # =========================================================
    #      ACCOUNT CREATION AND EMAIL VERIFICATION LOGIC
    # =========================================================

    def handle_create_account_click(self):
        """Handles the 'Create Account' button click."""
        # --- 1. Gather user input ---
        raw_full_name = self.create_account_page.fullName.text().strip()
        raw_email = self.create_account_page.email.text().strip().lower()
        raw_password = self.create_account_page.password.text()
        selected_program_text = self.create_account_page.comboBoxProgram.currentText()

        labelStatus = self.create_account_page.labelGeneralStatus
        # original_stylesheet = labelStatus.styleSheet()  # save original style

        # --- 2. Validate full name ---
        full_name_parts, name_error = validate_full_name(raw_full_name)
        if name_error:
            labelStatus.setText(name_error)
            self.set_label_color(labelStatus, "red")
            return
        full_name = " ".join(full_name_parts)  # store properly for DB

        # --- 3. Validate email ---
        email_error = validate_email(raw_email)
        if email_error:
            labelStatus.setText(email_error)
            self.set_label_color(labelStatus, "red")
            return

        # --- 4. Validate program selection ---
        program_map = {"Computer": "COMP", "Communication": "COMM", "Power": "PWM", "Biomedical": "BIO"}
        if selected_program_text == "Select":
            labelStatus.setText("Please select a program.")
            self.set_label_color(labelStatus, "red")
            return
        program_value = program_map[selected_program_text]

        # --- 5. Check for duplicate email in DB ---
        if self.db.check_email_exists(raw_email):
            self.create_account_page.highlight_invalid_lineedit(
                self.create_account_page.email, "Email already exists.")
            labelStatus.setText("Email already registered. Please Sign in.")
            self.set_label_color(labelStatus, "red")
            return

        # --- 6. Validation success: store new user data temporarily ---
        self.new_user_data = {
            "name": full_name,
            "email": raw_email,
            "password": raw_password,
            "program": program_value,
            "state": "student"  # default
        }

        # --- 7. Inform user and send verification code ---
        labelStatus.setText("All good! Please confirm your email...")
        self.set_label_color(labelStatus, "green")


        # --- 8. Initialize code generator (if not exists) ---
        if raw_email.lower() not in self.code_generators:
            self.code_generators[raw_email] = CodeGenerator(validity_minutes=5)

        self.email_sender = EmailSender()

        # --- 9. Generate & send code ---
        code_sent = self.send_verification_code(self.new_user_data["email"])

        if code_sent:
            print(f"Verification code sent: {self.code_generators[raw_email].code}")

        # --- 10. Go to confirmation page ---
        QTimer.singleShot(1500, self.go_to_confirm_email)


    def send_verification_code(self, to_email: str) -> bool:
        """
        Generates a fresh code for the given email (or reuses existing generator)
        and sends it via email.
        """
        if to_email not in self.code_generators:
            self.code_generators[to_email] = CodeGenerator(validity_minutes=5)

        generator = self.code_generators[to_email]
        code = generator.generate_verification_code()  # updates timestamp

        subject = "Your Verification Code"
        body = f"Your verification code is: {code}\nExpires in {generator.validity_minutes} minutes."

        sent = self.email_sender.send_email(to_email, subject, body)

        if sent:
            QMessageBox.information(self, "Code Sent", "A verification code was sent to your email.")
            self.confirm_email_page.start_cooldown_timer()
        else:
            QMessageBox.critical(self, "Error", "Failed to send verification email.")

        return sent
    
    # ----------------------------------------------------------
    #           EMAIL CONFIRMATION LOGIC
    # ----------------------------------------------------------
    def check_is_code_valid(self, entered_code: str, email: str) -> tuple[bool, str]:
        if not entered_code:
            return False, "Code cannot be empty."

        generator = self.code_generators.get(email)
        if not generator:
            return False, "No code generated for this email."

        print("DEBUG: generator.code =", generator.code)
        print("DEBUG: generator.expires_at =", getattr(generator, "expires_at", None))
        print("DEBUG: now =", __import__('datetime').datetime.now())

        if entered_code != generator.code:
            return False, "Incorrect verification code."

        if generator.is_code_expired():
            return False, "The code has expired. Please request a new one."

        return True, ""


    def handle_email_confirmation(self):
        entered_code = self.confirm_email_page.lineEditVerificationCode.text().strip()
        email = self.new_user_data["email"]

        is_valid, reason = self.check_is_code_valid(entered_code, email)

        if not is_valid:
            self.shake_widget(self.confirm_email_page.lineEditVerificationCode)
            self.highlight_invalid_lineedit(self.confirm_email_page.lineEditVerificationCode, reason)
            self.confirm_email_page.lineEditVerificationCode.setFocus()
            if reason != "Code cannot be empty.":
                QMessageBox.warning(self, "Invalid Code", reason)
            return
        

        # ------------------------------

        # ORIGINAL ACCOUNT CREATION LOGIC CONTINUES BELOW

        # Code valid – proceed to create account
        QMessageBox.information(self, "Code Verified", "Email verified successfully!")

        # Hash password and save to DB
        password_hashed = hash_password(self.new_user_data["password"])
        result = self.db.add_users(
            self.new_user_data["name"],
            self.new_user_data["email"],
            password_hashed,
            self.new_user_data["program"],
            self.new_user_data["state"]
        )

        if "successfully" in result:
            QMessageBox.information(self, "Email Confirmed",
                                    "Account created! Please wait for admin approval.")
            QTimer.singleShot(1000, self.go_to_login)
        else:
            QMessageBox.critical(self, "Error", f"An error occurred: {result}")

    # --- resend code logic ---
    def resend_code(self):
        email = self.new_user_data["email"]
        sent = self.send_verification_code(email)
        if sent:
            QMessageBox.information(self, "Code Sent", "Verification code resent successfully.")


    # =========================================================
    #               BACK NAVIGATION
    # =========================================================
    def handle_back_to_create_account(self):
        response = self.show_confirmation(
            "Are you sure?",
            "Going back might cancel the registration process."
        )
        if response == QMessageBox.StandardButton.Yes:
            self.go_to_create_account()

    def handle_back_to_sign_in(self):
        response = self.show_confirmation(
            "Are you sure?",
            "Going back might cancel the registration process."
        )
        if response == QMessageBox.StandardButton.Yes:
            self.go_to_login()

    # =========================================================
    #              RESET PASSWORD LOGIC
    # =========================================================

    def handle_password_reset_request(self):
        email_input = self.reset_password_page.ui.lineEditRegisteredEmail.text().strip().lower()

        # ----- Basic validation -----
        if not email_input:
            self.shake_widget(self.reset_password_page.ui.lineEditRegisteredEmail)
            self.highlight_invalid_lineedit(
                self.reset_password_page.ui.lineEditRegisteredEmail,
                "Please enter your registered email."
            )
            return

        # ----- Check if email exists in DB -----
        if not self.db.check_email_exists(email_input):
            self.shake_widget(self.reset_password_page.ui.lineEditRegisteredEmail)
            self.highlight_invalid_lineedit(
                self.reset_password_page.ui.lineEditRegisteredEmail,
                "Email not found."
            )
            QMessageBox.warning(self, "Error", "Email not found in our database.")
            return

        # Store email for reset flow
        self.reset_email = email_input

        # Create generator for this email if not exists
        if email_input not in self.reset_code_generators:
            self.reset_code_generators[email_input] = CodeGenerator(validity_minutes=5)

        self.email_sender = EmailSender()

        # ----- Send verification code -----
        sent = self.send_reset_code(email_input)
        if sent:
            QMessageBox.information(self, "Code Sent", "A verification code has been sent.")
            self.ui.stackedWidgetAuth.setCurrentWidget(self.reset_password_page)
            self.reset_password_page.start_cooldown_timer()



    # ----------------------------------------------------------
    #           SEND VERIFICATION CODE FOR RESET
    # ----------------------------------------------------------
    def send_reset_code(self, to_email: str) -> bool:
        # Use existing generator
        generator = self.reset_code_generators[to_email]

        # Generate new code + update timestamp
        code = generator.generate_verification_code()

        subject = "Password Reset Code"
        body = f"Your verification code is: {code}\nExpires in {generator.validity_minutes} minutes."

        sent = self.email_sender.send_email(to_email, subject, body)

        if sent:
            self.reset_password_page.start_cooldown_timer()
        else:
            QMessageBox.critical(self, "Error", "Failed to send reset code.")

        return sent
    
    def check_reset_code_valid(self, entered_code: str, email: str) -> tuple[bool, str]:
        if not entered_code:
            return False, "Code cannot be empty."

        generator = self.reset_code_generators.get(email)
        if not generator:
            return False, "No code generated for this email."

        if entered_code != generator.code:
            return False, "Incorrect verification code."

        if generator.is_code_expired():
            return False, "The code has expired. Please request a new one."

        return True, ""

    def handle_reset_code_confirmation(self):
        entered_code = self.reset_password_page.ui.lineEditCode.text().strip().lower()
        email = self.reset_email

        is_valid, reason = self.check_reset_code_valid(entered_code, email)
        if not is_valid:
            self.shake_widget(self.reset_password_page.ui.lineEditCode)
            self.highlight_invalid_lineedit(self.reset_password_page.ui.lineEditCode, reason)
            self.reset_password_page.ui.lineEditCode.setFocus()
            if reason != "Code cannot be empty.":
                QMessageBox.warning(self, "Invalid Code", reason)
            return

        # Open the dialog
        dialog = PasswordChangeDialog()
        
        # Connect the dialog button directly
        dialog.ui.buttonChangePassword.clicked.connect(
            lambda: self.update_password_from_dialog(dialog, email)
        )

        dialog.exec()

    def update_password_from_dialog(self, dialog: PasswordChangeDialog, email: str):
        new_pw = dialog.ui.lineEditPassword.text()
        
        # Fetch user and update
        user = self.db.get_user_by_login(email)
        if not user:
            QMessageBox.critical(dialog, "Error", "User not found.")
            return

        user_id, *_ = user
        hashed_pw = hash_password(new_pw)
        result = self.db.reset_password_with_email(user_id, email, hashed_pw)

        if "Error" not in result:
            QMessageBox.information(dialog, "Success", "Password updated successfully.")
            dialog.accept()  # closes the dialog
            self.go_to_login()  # return to login page
        else:
            QMessageBox.critical(dialog, "Error", result)

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthenticationWindow() 
    window.show()
    sys.exit(app.exec())
