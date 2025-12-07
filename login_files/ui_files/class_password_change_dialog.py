import os, sys
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QDialog, QApplication, QMessageBox

from login_files.ui_files.raw_ui.ui_password_change_dialog import Ui_PasswordChangeDialog
from helper_files.shared_utilities import BaseLoginForm # helper class that adds multitude of things



class PasswordChangeDialog(QDialog, BaseLoginForm):
    def __init__(self):
        super().__init__()
        self.ui = Ui_PasswordChangeDialog()
        self.ui.setupUi(self)  # setup the UI on this QWidget

        # Signal Slotting
        self.buttonChangePassword = self.ui.buttonChangePassword
        self.buttonCancel = self.ui.buttonCancel
        # line edits
        self.lineEditPassword = self.ui.lineEditPassword
        self.lineEditPasswordConfirm = self.ui.lineEditPasswordConfirm
        # pwrd authenticatuiins
        self.progressBarPwrdStrength = self.ui.progressBarPwrdStrength
        self.labelPwrdStrengthStatus = self.ui.labelPwrdStrengthStatus
        self.labelPasswordRules = self.ui.labelPasswordRules


        # Apply shadow to buttons
        self.add_shadow(self.buttonChangePassword)
        self.add_shadow(self.buttonCancel)
        # Shadow for the Login Panel/Qframe
        self.add_shadow(self.ui.passwordChangePanel, blur=25, xOffset=0, yOffset=5, color=(0, 0, 0, 120))


        # --- Show/hide password toggle button ---
        self.create_pwrd_toggle_button(self.lineEditPassword)
        self.create_pwrd_toggle_button(self.lineEditPasswordConfirm)
        
        # --- Connect password field to strength checker ---
        self.attach_password_strength_checker(
            self.lineEditPassword,
            self.progressBarPwrdStrength,
            self.labelPwrdStrengthStatus,
            self.labelPasswordRules
            )
        
        # -- attach confirm password checker--
        # highlights fields in red if passwords dont match
        self.attach_confirm_password_validator(
            self.lineEditPassword,
            self.lineEditPasswordConfirm
            )

        # --- Connect field changes to change password button state ---
        self.lineEditPassword.textChanged.connect(self.update_change_password_btn_state)
        self.lineEditPasswordConfirm.textChanged.connect(self.update_change_password_btn_state)

        # Initial button state disabled till fields are filled
        self.buttonChangePassword.setEnabled(False)

        # Make Cancel Button work
        self.buttonCancel.clicked.connect(self.handle_cancel_click)
        
    def handle_cancel_click(self):
        
        clikced_button = self.show_confirmation("Cancel?", "Are you sure you want to cancel password change proccess?")
        
        if clikced_button == QMessageBox.StandardButton.Yes:
            self.reject()

    def update_change_password_btn_state(self):
        """
        Enable Change password button only if:
        - all fields are filled
        - passwords match
        - combobox selected
        - password is strong and passes all rules
        """
        from helper_files.shared_utilities import all_fields_filled, passwords_match
        fields_ok = all_fields_filled([
            self.lineEditPassword.text(),
            self.lineEditPasswordConfirm.text()
        ])
        passwords_ok = passwords_match(self.lineEditPassword.text(), self.lineEditPasswordConfirm.text())

        # Password strength flag set by attach_password_strength_checker
        strong_pw = getattr(self, "password_is_strong", False)

        if fields_ok and passwords_ok and strong_pw:
            self.buttonChangePassword.setEnabled(True)
            self.buttonChangePassword.setToolTip("Ready to change password.")
        else:
            self.buttonChangePassword.setEnabled(False)
            self.buttonChangePassword.setToolTip("Please make sure all required fields are valid.")



    



if __name__ == "__main__":
    app = QApplication([])
    dialog = PasswordChangeDialog()
    dialog.exec()  # modal dialog
