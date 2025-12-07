import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from login_files.ui_files.raw_ui.ui_confirm_email_widget import Ui_ConfirmEmailWidget
from helper_files.shared_utilities import BaseLoginForm # helper class that adds multitude of things

import login_files.login_resources_rc


class ConfirmEmailWidget(BaseLoginForm):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ConfirmEmailWidget()
        self.ui.setupUi(self)  # setup the UI on this QWidget

        # for signaling and slotting
        self.buttonReSendCode = self.ui.buttonReSendCode
        self.buttonVerifyCode = self.ui.buttonVerifyCode
        self.buttonBackToCreateAccount = self.ui.buttonBackToCreateAccount
        self.buttonBackToSignIn = self.ui.buttonBackToSignIn
        self.lineEditVerificationCode = self.ui.lineEditVerificationCode
        self.labelTimer = self.ui.labelTimer

        # visual shadows
        self.add_shadow(self.buttonBackToSignIn)
        self.add_shadow(self.buttonReSendCode)
        self.add_shadow(self.buttonVerifyCode)
        self.add_shadow(self.ui.confirmEmailPanel)
        self.add_shadow(self.buttonBackToCreateAccount)

        # add a hide/show toggle button for verification code lineEdit

        self.create_pwrd_toggle_button(self.lineEditVerificationCode)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 60  # seconds

        # Disable resend until time ends
        self.ui.buttonReSendCode.setEnabled(False)

    def start_cooldown_timer(self):
        """Sets initial time
            Prepares UI
            Starts the QTimer
            """
        self.time_left = 60
        self.ui.labelTimer.setText("60")
        self.timer.start(1000)
        self.ui.buttonReSendCode.setEnabled(False)

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
            self.ui.buttonReSendCode.setEnabled(True)
        

if __name__ == "__main__":
    app = QApplication([])
    window = ConfirmEmailWidget()
    window.show()
    app.exec()
