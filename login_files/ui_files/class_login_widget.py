import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QIcon

from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsDropShadowEffect, QFrame, QHBoxLayout, QPushButton

from login_files.ui_files.raw_ui.ui_login_widget import Ui_LoginWidget
from helper_files.shared_utilities import BaseLoginForm # helper class that adds multitude of things

import login_files.login_resources_rc


class LoginWidget(BaseLoginForm):
    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginWidget()
        self.ui.setupUi(self)  # setup the UI on this QWidget

        # new line added trying to signalslot in auth window
        self.buttonCreateAccount = self.ui.buttonCreateAccount
        self.buttonLogin = self.ui.buttonLogin
        self.lineEditUsername = self.ui.lineEditUsername
        self.buttonResetPassword = self.ui.buttonResetPassword
        self.lineEditPassword = self.ui.lineEditPassword
        self.labelGeneralStatus = self.ui.labelGeneralStatus


        # Apply shadow to buttons
        self.add_shadow(self.buttonLogin)
        self.add_shadow(self.buttonCreateAccount)
        # Shadow for checkbox
        self.add_shadow(self.ui.checkBoxRemember, blur=8, xOffset=0, yOffset=2, color=(0, 0, 0, 80))
        # Shadow for the Login Panel/Qframe
        self.add_shadow(self.ui.loginPanel, blur=25, xOffset=0, yOffset=5, color=(0, 0, 0, 120))


        # --- Show/hide password toggle button ---
        self.create_pwrd_toggle_button(self.lineEditPassword)
        

if __name__ == "__main__":
    app = QApplication([])
    window = LoginWidget()
    window.show()
    app.exec()
