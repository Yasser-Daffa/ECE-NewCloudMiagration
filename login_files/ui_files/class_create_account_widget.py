import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QApplication

from helper_files.shared_utilities import BaseLoginForm
from login_files.ui_files.raw_ui.ui_create_account_widget import Ui_CreateAccountWidget
import login_files.login_resources_rc



class CreateAccountWidget(BaseLoginForm):
    def __init__(self):
        super().__init__()
        self.ui = Ui_CreateAccountWidget()
        self.ui.setupUi(self)  # setup the UI on this QWidget


        # Store frequently used widgets in shortcuts
        self.buttonCreateAccont = self.ui.buttonCreateAccount
        self.fullName = self.ui.lineEditFullName
        self.email = self.ui.lineEditEmail
        self.password = self.ui.lineEditPassword
        self.confirm = self.ui.lineEditPasswordConfirm
        self.comboBoxProgram = self.ui.comboBoxSelectProgram
        self.buttonLoginHere = self.ui.buttonLoginHere
        self.labelGeneralStatus = self.ui.labelGeneralStatus

        # pwrd authenticatuiins
        self.progressBarPwrdStrength = self.ui.progressBarPwrdStrength
        self.labelPwrdStrengthStatus = self.ui.labelPwrdStrengthStatus
        self.labelPasswordRules = self.ui.labelPasswordRules
        
        

        # ---------------------------
        # UI tweaks
        # ---------------------------

        # Disable mouse wheel scrolling for this combobox to avoid annoyance
        self.ui.comboBoxSelectProgram.wheelEvent = lambda event: event.ignore()
        self.add_shadow(self.buttonCreateAccont)
        self.add_shadow(self.ui.loginPanel, blur=25, yOffset=5, color=(0,0,0,120))

        # Disable button initially
        self.buttonCreateAccont.setEnabled(False)
        self.buttonCreateAccont.setToolTip("Please make sure all required fields are filled.")
        

        # ---------------------------
        # Connect field changes to button state
        # ---------------------------
        for lineEdits in [
            self.fullName,
            self.email,
            self.password,
            self.confirm
            ]:

            lineEdits.textChanged.connect(self.update_create_btn_state)

        self.comboBoxProgram.currentIndexChanged.connect(self.update_create_btn_state)
        self.comboBoxProgram.activated.connect(lambda: self.attach_combobox_validator(self.comboBoxProgram))


        # ---------------------------
        # Show/hide password toggles
        # ---------------------------
        # Create toggle buttons for password fields
        self.create_pwrd_toggle_button(self.ui.lineEditPassword)
        self.create_pwrd_toggle_button(self.ui.lineEditPasswordConfirm)

        # ---------------------------
        # Password matching
        # ---------------------------
        self.attach_confirm_password_validator(self.password, self.confirm)

        # ---------------------------
        # Password strength & rule checker
        # ---------------------------
        self.attach_password_strength_checker(
            self.password,
            self.progressBarPwrdStrength,
            self.labelPwrdStrengthStatus,
            self.labelPasswordRules
            )

    # --------------------------------
    # Update "Create Account" button state
    # --------------------------------
    def update_create_btn_state(self):
        """
        Enable create button only if:
        - all fields are filled
        - passwords match
        - combobox selected
        - password is strong and passes all rules
        """
        from helper_files.shared_utilities import all_fields_filled, passwords_match
        fields_ok = all_fields_filled([
            self.fullName.text().strip(),
            self.email.text().strip(),
            self.password.text(),
            self.confirm.text()
        ])
        passwords_ok = passwords_match(self.password.text(), self.confirm.text())
        program_ok = self.validate_combobox_selection(self.comboBoxProgram)

        # Password strength flag set by attach_password_strength_checker
        # getattr gets attribute if exists, else returns False
        # its useful to avoid attribute errors if the attribute is not set yet
        strong_pw = getattr(self, "password_is_strong", False)

        if fields_ok and passwords_ok and program_ok and strong_pw:
            self.buttonCreateAccont.setEnabled(True)
            self.buttonCreateAccont.setToolTip("Ready to create account.")
        else:
            self.buttonCreateAccont.setEnabled(False)
            self.buttonCreateAccont.setToolTip("Please make sure all required fields are valid.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CreateAccountWidget() 
    window.show()
    sys.exit(app.exec())

