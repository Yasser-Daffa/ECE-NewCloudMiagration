import os, sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsDropShadowEffect, QFrame, QHBoxLayout, QPushButton
import sys

from login_files.ui_files.raw_ui.ui_reset_password_widget import Ui_ResetPasswordWidget
from helper_files.shared_utilities import BaseLoginForm
import login_files.login_resources_rc

class ResetPasswordWidget(BaseLoginForm):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ResetPasswordWidget()
        self.ui.setupUi(self)  # setup the UI on this QWidget
        
        # for signaling and slotting
        self.buttonSendCode = self.ui.buttonSendCode
        self.buttonVerifyCode = self.ui.buttonVerifyCode
        self.buttonBackToSignIn = self.ui.buttonBackToSignIn
        self.lineEditRegisteredEmail = self.ui.lineEditRegisteredEmail
        self.lineEditCode = self.ui.lineEditCode
        self.labelTimer = self.ui.labelTimer
        

        # visual shadows
        self.add_shadow(self.buttonBackToSignIn)
        self.add_shadow(self.buttonSendCode)
        self.add_shadow(self.buttonVerifyCode)
        self.add_shadow(self.ui.resetPasswordPanel)

        # add a hide/show toggle button for verification code lineEdit
        self.create_pwrd_toggle_button(self.lineEditCode)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 60  # seconds

        # Disable resend until time ends
        self.attach_non_empty_validator(self.lineEditRegisteredEmail)
        self.attach_non_empty_validator(self.lineEditCode)


        self.buttonSendCode.setEnabled(False)

        self.lineEditRegisteredEmail.textChanged.connect(
            lambda: self.update_button_state(self.lineEditRegisteredEmail, self.buttonSendCode))
        

        self.buttonVerifyCode.setEnabled(False)

        self.lineEditCode.textChanged.connect(
            lambda: self.update_button_state(self.lineEditCode, self.buttonVerifyCode))
        
        # Editing the time text initially
        self.labelTimer.setText("Click to request code")

    def start_cooldown_timer(self):
        """Sets initial time
            Prepares UI
            Starts the QTimer
            """
        self.time_left = 60
        self.ui.labelTimer.setText("60")
        self.timer.start(1000)
        self.ui.buttonSendCode.setEnabled(False)

    def update_timer(self):
        """ Purpose of this method is to update the countdown timer decrementally
        Runs every second
        Handles countdown logic
        Stops timer when finished (replaces it with text)
        """
        self.time_left -= 1
        self.ui.labelTimer.setText(str(self.time_left))

        if self.time_left <= 0:
            self.timer.stop()
            self.ui.labelTimer.setText("You can request a new code now.")
            self.ui.buttonSendCode.setEnabled(True)

    def update_button_state(self, line_edit, button):
        """updates send code button till lineEdit is filled"""
        text = line_edit.text().strip()
        button.setEnabled(bool(text))


if __name__ == "__main__":
    app = QApplication([])
    window = ResetPasswordWidget()
    window.show()
    app.exec()