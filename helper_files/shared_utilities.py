# HELPER-FUNCTIONS
# ----------------
# This file contains reusable helper functions and a base form class
# that provide:
# 1. BaseLoginForm Class that contains the following Methods
#   1- Password hide/show toggle functionality
#   2- Border highlighting for invalid inputs
#   3- Attatchement Methods for field validators
#   4- Password Strength check functionality
#   5- Adds Shadow and animation methods for widgets
#   6- Reusable confirmation dialog method

# 2. "SendEmail" Class to send emails
#   - set_sender_email; to set the email responsable of sending msgs
#       NOTE: Yasser's email is the default here
#   - get_sender_email; if you want to view the sender's email
#   - set_app_password; needed to actuate the sending of emails
# ----------------------


from PyQt6.QtCore import Qt, QEvent, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGraphicsDropShadowEffect, QFrame,
    QHBoxLayout, QPushButton, QComboBox, QLineEdit, QMessageBox
)
import random
import smtplib
from datetime import datetime, timedelta

import login_files.login_resources_rc


# -----------------------------
# SIMPLE FIELD VALIDATORS
# -----------------------------
def all_fields_filled(fields) -> bool:
    """
    Checks if all fields in the given list are non-empty.
    
    'fields' should be a list of (field_name, field_value) tuples.
    
    Returns True if all values are non-empty, False otherwise.
    
    Example usage:
        username = "user123"
        email = "user@example.com"
        password = ""
        fields = [(username), (email), (password)]
        
        if all_fields_filled(fields):
            print("All fields are filled!")
        else:
            print("Some fields are missing!")
        # Output: Some fields are missing!
    """
    return all(str(field_value).strip() != "" for field_value in fields)


def passwords_match(password: str, password_confirm: str) -> bool:
    """
    Checks if the password and its confirmation match.
    """
    return password == password_confirm and password != ""


# -----------------------------
#       BASE FORM CLASS
# -----------------------------
class BaseLoginForm(QWidget):
    """Base class with shared methods for forms like CreateAccountWidget."""
    from PyQt6.QtWidgets import QLineEdit
    def __init__(self, parent=None):
        super().__init__(parent)

        
        # Stores each toggle button, keyed by its QLineEdit.
        # Example: toggle_buttons[line_edit] = toggle_btn
        self.toggle_buttons = {}

        # Stores whether each password field is currently visible (True) or hidden (False).
        # We track this ourselves because QLineEdit/QPushButton don't hold this state.
        self.show_password_states = {}

        # These dictionaries let the same toggle logic work for any number of password fields.
        # If future forms have more password boxes, the same code will handle them automatically.
        # This allows the BaseLoginForm to support unlimited password fields without writing new code.
    

    # -------------------------------
    # 1. PASSWORD HIDE/SHOW TOGGLE BUTTONS
    # -------------------------------

    def create_pwrd_toggle_button(self, line_edit: QLineEdit):
        """
        Creates an eye-icon toggle button inside a QLineEdit to show/hide password.
        The button automatically toggles the line_edit's echo mode when clicked.
        """
        btn = QPushButton(line_edit)
        btn.setIcon(QIcon(":/qrc_images/assets/images/open_eye_icon24.png"))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.setFixedSize(24, 24)
        btn.setStyleSheet("border: none; background: transparent;")
        btn.clicked.connect(lambda: self.toggle_password(line_edit))

        # KEEP track of states
        self.toggle_buttons[line_edit] = btn
        self.show_password_states[line_edit] = False

        # initial position
        self.update_toggle_button_position(line_edit)

        # schedule the update after the layout is applied.
        # otherwise it will result in a missplacement on initial launch of the window
        # try commenmting these line and seeing for yourself
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.update_toggle_button_position(line_edit))
        #-----------------

            # CRITICAL FIX: update when the LINE EDIT resizes  
        orig_resize = line_edit.resizeEvent
        def new_resize(event):
            orig_resize(event)
            self.update_toggle_button_position(line_edit)

        line_edit.resizeEvent = new_resize

        return btn

    def toggle_password(self, line_edit: QLineEdit):
        """
        Toggles the visibility of the password for a given QLineEdit.
        Updates the icon accordingly.
        """
        state = self.show_password_states[line_edit]
        if state:
            # Hide password
            line_edit.setEchoMode(self.QLineEdit.EchoMode.Password)
            self.toggle_buttons[line_edit].setIcon(QIcon(":/qrc_images/assets/images/open_eye_icon24.png"))
        else:
            # Show password
            line_edit.setEchoMode(self.QLineEdit.EchoMode.Normal)
            self.toggle_buttons[line_edit].setIcon(QIcon(":/qrc_images/assets/images/close_eye_icon24.png"))
        # Toggle the state
        self.show_password_states[line_edit] = not state


    def update_toggle_button_position(self, line_edit: QLineEdit):
        """ The calculations required to Move toggle button 
        to the correct position inside the line edit."""
        btn = self.toggle_buttons[line_edit]

        x = line_edit.width() - btn.width() - 4
        y = (line_edit.height() - btn.height()) // 2

        btn.move(x, y)


    def resizeEvent(self, event):
        """Reposition ALL toggle buttons when window resizes."""
        super().resizeEvent(event)
        for line_edit in self.toggle_buttons:
            self.update_toggle_button_position(line_edit)


    # -----------------------------
    # 2. BORDER HIGHLIGHTING METHODS
    # -----------------------------
    # We should use these if we only want validations


    ## NOTE:
    # - Each QLineEdit may already have a custom style applied (colors, borders, fonts).
    #   If we just set a red border directly, it would overwrite any existing styles.

    # - To prevent that, we store the original style in a custom attribute on the widget itself:
    #       _original_style = line_edit.styleSheet()

    # - Before applying the red border, we check if this attribute exists using hasattr(line_edit, "_original_style").
    #   - If it exists, we reuse it so we don't overwrite previous styles.
    #   - If it doesn't exist, we save the current style first.
    # - This allows us to easily reset the field back to its original appearance later.

    def highlight_invalid_lineedit(self, line_edit: QLineEdit, message: str):
        """
        Set a red border and tooltip for any invalid QLineEdit.

        Parameters:
        - line_edit: The QLineEdit widget to highlight.
        - message: The tooltip message to show when invalid.
        
        Notes:
        - We store the original stylesheet on the widget itself using a custom
        attribute '_original_style'. This prevents overwriting existing styles.
        - hasattr(line_edit, "_original_style") checks if we have already stored it.
        """
        if not hasattr(line_edit, "_original_style"):
            # Save the original style to restore later
            line_edit._original_style = line_edit.styleSheet()

        # Append a red border style while keeping the original styles
        line_edit.setStyleSheet(
            line_edit._original_style +
            "QLineEdit { border: 2px solid red; } QLineEdit:focus { border: 2px solid red; }"
        )
        # Set tooltip for user guidance
        line_edit.setToolTip(message)


    def reset_lineedit_border(self, line_edit: QLineEdit):
        """
        Reset a QLineEdit's border to its original style.

        - Only resets if we have stored the original style previously.
        - Clears any tooltip message.
        """
        if hasattr(line_edit, "_original_style"):
            line_edit.setStyleSheet(line_edit._original_style)
            line_edit.setToolTip("")


    def validate_confirm_password(self, password_line: QLineEdit, confirm_line: QLineEdit):
        """
        Highlights the confirm password field in red if it doesn't match the main password.

        Parameters:
        - password_line: The main password QLineEdit.
        - confirm_line: The confirmation password QLineEdit.

        Uses:
        - passwords_match() from helper functions to compare values.
        - Calls highlight_invalid_lineedit / reset_lineedit_border accordingly.
        """
        from helper_files.shared_utilities import passwords_match

        password = password_line.text()
        confirm = confirm_line.text()

        if passwords_match(password, confirm):
            self.reset_lineedit_border(confirm_line)
        else:
            self.highlight_invalid_lineedit(confirm_line, "Passwords do not match.")


    def validate_non_empty(self, line_edit: QLineEdit, field_name: str = "This field"):
        """
        Highlights a QLineEdit in red if it is empty.

        Parameters:
        - line_edit: The QLineEdit to validate.
        - field_name: Optional friendly name for tooltip message.
        
        Usage:
        - Called on text change to give dynamic feedback.
        """
        if line_edit.text().strip() == "":
            self.highlight_invalid_lineedit(line_edit, f"{field_name} cannot be empty.")
            return False
        else:
            self.reset_lineedit_border(line_edit)
            return True

    def validate_combobox_selection(self, combo: QComboBox, message: str = "Please select a valid option."):
        """
        Highlights a QComboBox in red if no valid selection is made.

        - A valid selection is considered any index > 0 (common practice where index 0 = placeholder).
        - Uses a custom attribute '_original_style' to store original style for later restoration.

        Returns:
        - True if selection is valid.
        - False if invalid (and highlights the combo box in red).
        """
        if combo.currentIndex() <= 0:
            # Save original style if not already stored
            if not hasattr(combo, "_original_style"):
                combo._original_style = combo.styleSheet()

            combo.setStyleSheet(combo._original_style + "\nQComboBox { border: 2px solid red; }")
            combo.setToolTip(message)
            return False
        else:
            # Restore original style
            if hasattr(combo, "_original_style"):
                combo.setStyleSheet(combo._original_style)
                combo.setToolTip("")
            return True
        

        ## Example usage on how to use these methods
        ## inside some slot or validation function


    def set_label_color(self, label, color: str):
        """
        Sets the QLabel text color using the 'statusColor' property for QSS.
        color: 'red' or 'green' (or other values defined in your QSS)
        """
        label.setProperty("statusColor", color)
        label.style().unpolish(label)  # Force Qt to reapply the style
        label.style().polish(label)

    def reset_label_color(self, label):
        """Reset label to its original stylesheet."""
        if hasattr(label, "_original_style"):
            label.setStyleSheet(label._original_style)


# self.validate_non_empty(self.ui.lineEditUsername, "Username")
# self.validate_confirm_password(self.ui.lineEditPassword, self.ui.lineEditPasswordConfirm)
# self.validate_combobox_selection(self.ui.comboBoxRole)

    # -----------------------------
    # 3. DYNAMIC VALIDATION HOOKS
    # -----------------------------
    # These are the ones we should be using to check non empty fields
    # Or add a validator in general if we want live feedback 

    def attach_non_empty_validator(self, line_edit: QLineEdit, field_name: str = "This field"):
        """
        Attach dynamic validation to a QLineEdit that checks if it is non-empty.
        Updates the border in real-time as user types.
        """
        line_edit.textChanged.connect(lambda: self.validate_non_empty(line_edit, field_name))

    def attach_confirm_password_validator(self, password_line: QLineEdit, confirm_line: QLineEdit):
        """
        Attach dynamic validation between password and confirm password fields.
        Updates border in real-time while typing.
        """
        password_line.textChanged.connect(lambda: self.validate_confirm_password(password_line, confirm_line))
        confirm_line.textChanged.connect(lambda: self.validate_confirm_password(password_line, confirm_line))

    def attach_combobox_validator(self, combo: QComboBox, message: str = "Please select a valid option."):
        """
        Attach dynamic validation to a QComboBox that checks selection.
        Updates the border immediately on selection change.
        """
        combo.currentIndexChanged.connect(lambda _: self.validate_combobox_selection(combo, message))


    # -------------------------------
    # 4. PASSWORD STRENGTH CHECKER
    # -------------------------------

    def attach_password_strength_checker(
        self,
        password_line: QLineEdit,
        progress_bar,
        strength_label,
        rules_label
    ):
        """
        Attaches a dynamic password strength checker to a QLineEdit.

        Parameters:
        - password_line: QLineEdit for the password input
        - progress_bar: QProgressBar to display strength
        - strength_label: QLabel to show 'Weak/Moderate/Strong'
        - rules_label: QLabel to show password requirements, updates dynamically

        Behavior:
        - Updates strength label
        - Updates progress bar chunk color (preserving existing stylesheet)
        - Updates requirements label with * prefix and green/red color
        - Highlights password line edit red if requirements not met
        - Preserves original tooltips
        """
        from helper_files.validators import validate_password, validate_password_strength

        # Store original stylesheet to preserve it
        if not hasattr(progress_bar, "_original_style"):
            progress_bar._original_style = progress_bar.styleSheet() or ""

        def update_strength():
            password = password_line.text()
            valid, errors = validate_password(password)
            strength = validate_password_strength(password)

            # --- Update strength label ---
            strength_label.setText(strength)

            # --- Update progress bar value and color only ---
            strength_map = {"Weak": 25, "Moderate": 50, "Strong": 100}
            color_map = {"Weak": "#e74c3c", "Moderate": "#f39c12", "Strong": "#2ecc71"}
            progress_bar.setValue(strength_map[strength])

            # Only append color change to existing style
            progress_bar.setStyleSheet(
                progress_bar._original_style +
                f"""
                QProgressBar::chunk {{
                    background-color: {color_map[strength]};
                }}
                """
            )

            # --- Update requirements label dynamically ---
            requirements = [
                "Password must be at least 8 characters long.",
                "Password must contain at least one uppercase letter.",
                "Password must contain at least one lowercase letter.",
                "Password must contain at least one digit.",
                "Password must contain at least one special character."
            ]

            label_lines = []
            tooltip_lines = []

            for req in requirements:
                color = "green" if req not in errors else "red"
                label_lines.append(f'<span style="color:{color};">* {req}</span>')
                tooltip_lines.append(f'* {req}')

            rules_label.setText("<br>".join(label_lines))
            rules_label.setToolTip("\n".join(tooltip_lines))

            # --- Highlight password line edit if invalid ---
            if not valid:
                self.highlight_invalid_lineedit(password_line, "Password does not meet all requirements.")
            else:
                self.reset_lineedit_border(password_line)

            # Set flag for CreateAccountWidget to read
            # using setattr to dynamically create the attribute otherwise it wont exist
            setattr(self, "password_is_strong", valid and strength == "Strong")

        # Connect signal to update on text change
        password_line.textChanged.connect(update_strength)

        # Call once to initialize display
        update_strength()

        
# -------- EXAMPLE USAGE ---------
# self.attach_non_empty_validator(self.ui.lineEditUsername, "Username")
# self.attach_non_empty_validator(self.ui.lineEditEmail, "Email")
# self.attach_confirm_password_validator(self.ui.lineEditPassword, self.ui.lineEditPasswordConfirm)
# self.attach_combobox_validator(self.ui.comboBoxRole)

#-- EXAMPLE FOR THE "attach_password_stenghth_checker" method

# self.attach_password_strength_checker(
#     self.lineEditPassword,
#     self.progressBarPwrdStrength,
#     self.labelPwrdStrengthStatus,
#     self.labelPasswordRules
# )



    # -------------------------------
    # 5. SHADOW & ANIMATION HELPERS
    # -------------------------------

    def add_shadow(self, widget, blur=15, xOffset=0, yOffset=5, color=(0, 0, 0, 160)):
        """Adds a drop shadow effect to any QWidget"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setXOffset(xOffset)
        shadow.setYOffset(yOffset)
        shadow.setColor(QColor(*color))
        widget.setGraphicsEffect(shadow)

    def shake_widget(self, widget):
        """Simple shake animation for widgets (e.g., invalid input)"""
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        original_pos = widget.pos()
        offset = 6

        anim.setKeyValueAt(0, original_pos)
        anim.setKeyValueAt(0.25, original_pos + QPoint(-offset, 0))
        anim.setKeyValueAt(0.5, original_pos + QPoint(offset, 0))
        anim.setKeyValueAt(0.75, original_pos + QPoint(-offset, 0))
        anim.setKeyValueAt(1, original_pos)

        anim.start()
        self._shake_animation = anim  # Keep a reference to prevent garbage collection

    
    @staticmethod
    def animate_label_with_dots(label, base_text="Loading", interval=400, duration=None, on_finished=None):
        """
        Animate a QLabel with dots: base_text, base_text., base_text.., base_text...
        
        Parameters:
            label: QLabel to animate
            base_text: base string to display
            interval: timer interval in ms
            duration: optional total duration in ms; if None, runs indefinitely until stop()
            on_finished: optional function to call when animation stops
        
        Returns:
            timer instance (QTimer) so you can stop it externally
        """
        timer = QTimer()
        dots_counter = {"count": 0}  # mutable for closure

        def update_label():
            dots_counter["count"] = (dots_counter["count"] + 1) % 4
            label.setText(f"{base_text}{'.' * dots_counter['count']}")

        timer.timeout.connect(update_label)
        timer.start(interval)

        if duration is not None:
            def stop_timer():
                timer.stop()
                if on_finished:
                    on_finished()
            QTimer.singleShot(duration, stop_timer)

        return timer
    
    # Why @staticmethod:
    #   - This method does not use 'self' or any instance-specific data.
    #   - It purely works with the parameters passed to it.
    #   - Using @staticmethod allows us to call it directly on the class:
    #       BaseLoginForm.animate_label_with_dots(my_label)
    #       without needing to create an instance of UiHelpers.
    #   - This makes it reusable anywhere in the project without tying it to a specific object.
    

    # -------------------------------
    # 6. REUSABLE CONFIRMATION DIALOG
    # -------------------------------

    def show_confirmation(self, title: str, message: str):
        """
        Shows a reusable Yes/No confirmation dialog.

        Parameters
        ----------
        title : str
            The window title of the confirmation dialog.
        message : str
            The main message to show inside the dialog.

        Returns
        -------
        QMessageBox.StandardButton
            Returns the button the user clicked:
            - QMessageBox.StandardButton.Yes
            - QMessageBox.StandardButton.No

        Notes
        -----
        This method can be reused across any widget that inherits from BaseLoginForm.
        You can check the return value to trigger different actions based on user
        confirmation.
        """

        # Create the dialog
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Question)   # Info icon
        dialog.setWindowTitle(title)                   # Set dialog title
        dialog.setText(message)                        # Set main text

        # Add Yes / No buttons
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        # Execute dialog and capture clicked button
        clicked_button = dialog.exec()

        return clicked_button
    
## --- Example usage of show_confirmation method ---
# response = self.show_confirmation(
#     "Delete Account",
#     "Are you sure you want to delete this account?"
# )

# if response == QMessageBox.StandardButton.Yes:
#     self.delete_account()

# elif response == QMessageBox.StandardButton.No:
#     print("User canceled.")


# -----------------------------
#       EMAIL SENDER CLASS
# -----------------------------

class EmailSender:
    """Class to send emails using pre-configured SMTP credentials.

    methods:
        - sender_email: The email address used to send messages.
        - app_password: The app password for SMTP authentication.
        - generated_code: The last generated verification code.
        - code_generated_at: Timestamp when the code was generated.
    """
    code_validity_minutes = 5 # Code expires after 5 minutes

    def __init__(self):
        super().__init__()
        
        """
        Initialize the email sender with private SMTP credentials.
        These stay fixed for the entire application.
        """
        self.__SMTP_SERVER = "smtp.gmail.com"
        self.__SMTP_PORT   = 465
        self.__SMTP_USER   = "automailer.yasserdaffa@gmail.com"# SENDER EMAIL
        self.__SMTP_PASS   = "yqug utkt jiyx ohdt" # APP Password

        self.generated_code = None
        self.code_generated_at = None  # Timestamp when code was created
        

    # -----------------------------
    # Getter and Setter for Email
    # -----------------------------
    # @property here allows us to access the private attribute safely
    # and makes a method behave like an attribute
    
    # getter
    @property
    def sender_email(self):
        """Getter: allows access to the private __SMTP_USER attribute.

        ex. usage: email_sender = EmailSender()

                  print(email_sender.sender_email)  # Access via getter
        """
        return self.__SMTP_USER
    
    # setter
    @sender_email.setter
    def sender_email(self, new_email):
        """Setter: allows updating the private __SMTP_USER attribute safely.
        
        ex. usage: email_sender = EmailSender()

                  email_sender.sender_email = "new_email@example.com"
                  """
        print(f"Changing email → {new_email}")
        self.__SMTP_USER = new_email
    
    # -- example usage for setters and getters --
    # email_sender = EmailSender()
    # print(email_sender.sender_email)  # Access via getter
    # email_sender.sender_email = "new_email@example.com"  # Update via setter

    # -----------------------------
    # Setter for Password only
    # -----------------------------

    # getter is not provided to keep password hidden
    @property
    def app_password(self):
        """Setter-only placeholder. No getter provided to keep password hidden."""
        raise AttributeError("Password cannot be read directly.")
    
    # setter
    @app_password.setter
    def app_password(self, new_pass):
        """Setter: allows updating the private __SMTP_PASS attribute safely."""
        print("Setting new SMTP password.")
        self.__SMTP_PASS = new_pass


    # -----------------------------
    # SEND REGULAR EMAIL METHOD
    # -----------------------------

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Sends an email using pre-configured Gmail credentials.
        Returns:
            True  → if sent successfully
            False → if failed
        """

        import smtplib
        import ssl
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = self.__SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(self.__SMTP_SERVER,
                                  self.__SMTP_PORT,
                                  context=context) as server:
                server.login(self.__SMTP_USER, self.__SMTP_PASS)
                server.send_message(msg)

            return True
        except Exception:
            return False
    

# -----------------------------
# VERIFICATION CODE GENERATOR CLASS
# -----------------------------

class CodeGenerator:
    def __init__(self, validity_minutes: int = 5):
        self.validity_minutes = validity_minutes
        self.generated_at = None
        self.code = None  # <-- store last generated code
        self.expires_at: datetime | None = None

    def generate_verification_code(self):
        self.code = str(random.randint(100000, 999999))
        self.expiry_time = datetime.now() + timedelta(minutes=self.validity_minutes)
        return self.code

    def is_code_expired(self) -> bool:
        """Return True only if the code exists AND it's past the expiration time."""
        if self.expires_at is None:
            return False   # Not expired because no expiration was set yet
        return datetime.now() > self.expires_at

    
# -----------------------------
# Timer class for line edits
# -----------------------------

#CLASS IS UNUSED SO FAR
class CodeTimerMixin:
    """
    Mixin that provides:
    - A 60-second cooldown timer
    - Automatic countdown updates
    - Enabling/disabling the resend button

    This mixin does NOT handle sending emails.
    It only controls the UI behavior for timing.
    """

    def __init__(self, line_edit_widget, label_timer_widget, resend_button_widget):
        """
        Parameters:
            line_edit_widget: QLineEdit used for entering verification code
            label_timer_widget: QLabel used for showing remaining seconds
            resend_button_widget: QPushButton that is enabled when timer ends

        No return value. Initializes internal timer + disables resend button.
        """
        self.lineEditVerificationCode = line_edit_widget
        self.labelTimer = label_timer_widget
        self.buttonReSendCode = resend_button_widget

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.time_left = 60  # countdown seconds
        self.buttonReSendCode.setEnabled(False)  # disabled until timer finishes

    # ----------------------------------------------------------
    def start_cooldown_timer(self):
        """
        Starts the 60-second cooldown:
        - Resets timer to 60
        - Updates label
        - Starts 1-second ticks
        - Disables resend button

        No return value.
        """
        self.time_left = 60
        self.labelTimer.setText("60")
        self.timer.start(1000)
        self.buttonReSendCode.setEnabled(False)

    # ----------------------------------------------------------
    def update_timer(self):
        """
        Called automatically every 1 second.
        Updates countdown UI and re-enables resend button when done.

        No return value.
        """
        self.time_left -= 1
        self.labelTimer.setText(str(self.time_left))

        if self.time_left <= 0:
            self.timer.stop()
            self.labelTimer.setText("You can request a new code now.")
            self.buttonReSendCode.setEnabled(True)


# -----------------------------
# Custom show_message box as the defaul QMessageBox doesnt work well with windows dark mode
# -----------------------------
from PyQt6.QtGui import QPalette, QColor

# Import icons for easier usage
Warning = QMessageBox.Icon.Warning
Information = QMessageBox.Icon.Information
Critical = QMessageBox.Icon.Critical

def show_msg(parent, title, text, icon=Information):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)

    # Force colors: white bg, black text
    palette = msg.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("white"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    msg.setPalette(palette)
    msg.setStyleSheet("QLabel{color: black;} QPushButton{background-color: white; color: black;}")

    msg.exec()

#Example usage
# 
# show_msg(self.dialog, "Error", "Please select a course first.", icon=Warning)
#


# ------------------- EASY-TO-USE FUNCTIONS *instead of the one above use these -------------------
def warning(parent, text):
    show_msg(parent, "Warning", text, QMessageBox.Icon.Warning)

def info(parent, text):
    show_msg(parent, "Info", text, QMessageBox.Icon.Information)

def error(parent, text):
    show_msg(parent, "Error", text, QMessageBox.Icon.Critical)


# Example usage
#if not self.selected_course:
#    warning(self.dialog, "Please select a course first.")