import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from PyQt6.QtCore import QTimer

from PyQt6 import QtWidgets
from database_files.cloud_database import is_connected_to_db

from student.class_student_utilities import StudentUtilities
from admin.class_admin_utilities import AdminUtilities

# Subpage UI & Controller imports
from app_ui.student_ui.ui_student_dashboard import Ui_StudentDashboard

# # not finished yet
# from app_ui.student_ui.submenus_ui.ui_profile import Ui_Profile
from student.submenus.class_profile import ProfileWidget

from student.submenus.class_current_schedule import CurrentScheduleWidget

from student.submenus.class_register_courses import RegisterCoursesWidget

from student.submenus.class_view_prereqs import ViewPrereqsWidget

from student.submenus.class_view_program_plans import ViewProgramPlansWidget

from student.submenus.class_transcript import TranscriptWidget



# CANT TEST THIS CLASS IN HERE UNLESS WE HAVE THE REQUIRED INFORMATION FROM USERS

class StudentDashboard(QtWidgets.QMainWindow):
    """
    Main admin dashboard window.
    Handles page switching via a QStackedWidget and initializes all sub-pages.
    """
    
    def __init__(self, db, user_info):
        super().__init__()

        # -------------------------------
        # Main UI setup
        # -------------------------------
        self.ui = Ui_StudentDashboard()
        self.ui.setupUi(self)

        self.db = db
        self.user_info = user_info
        (
            self.user_id,
            self.name,
            self.email,
            self.program,
            self.state,
            self.account_status,
            self.hashed_pw,
        ) = user_info

        # Shared utilities
        self.student = StudentUtilities(self.db, self.user_id)
        self.admin_utils = AdminUtilities(self.db)

        # Displays the name at the top-left side near the pfp
        self.ui.labelStudentName.setText(self.name)

        # Get last login (Last online) from stored in database from authentication window :]
        last_login = self.db.get_last_login(self.user_id)

        if last_login:
            self.ui.labelLastLogin.setText(f"Last Login: {last_login}")
        else:
            self.ui.labelLastLogin.setText("Last Login: First Time")

        # ------------------------
        # 1. Initialize all pages
        # ------------------------
        self.init_sub_pages()

        # ------------------------
        # 2. Add pages to stacked widget
        # ------------------------
        self.ui.stackedWidget.addWidget(self.profile_page)
        self.ui.stackedWidget.addWidget(self.current_schedule_page)
        self.ui.stackedWidget.addWidget(self.register_courses_page)
        self.ui.stackedWidget.addWidget(self.view_prereqs_page)
        self.ui.stackedWidget.addWidget(self.view_program_plans_page)
        self.ui.stackedWidget.addWidget(self.transcript_page)

        # Add other pages similarly...


        # -------------------------------
        # 3- Map buttons to their corresponding pages
        # -------------------------------

        # Key: QPushButton object
        # Value: Tuple of (page name string, QWidget page)
        # Using a string here avoids printing emojis/unicode directly from button.text()
        self.page_mapping = {
            self.ui.buttonProfile: ("Profile", self.profile_page),
            self.ui.buttonCurrentSchedule: ("Current Schedule", self.current_schedule_page),
            self.ui.buttonRegisterCourses: ("Manage Courses", self.register_courses_page),
            self.ui.buttonViewPrereqs: ("View Prereqs", self.view_prereqs_page),
            self.ui.buttonViewProgramPlans: ("View Program Plans", self.view_program_plans_page),
            self.ui.buttonTranscript: ("Transcript", self.transcript_page),
        }

        # Connect buttons to page-switching logic
        for button in self.page_mapping.keys():
            button.clicked.connect(lambda checked, b=button: self.switch_to_page(b))

        # Connect logout button
        self.ui.buttonLogout.clicked.connect(self.fade_and_logout)

        # Show default page (should be profile first)
        self.switch_to_page(self.ui.buttonProfile)
        # updates connection status label based on user's connection to cloud database
        # Update status once now
        self.update_connection_status()

        # Auto refresh every 5 seconds
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(5000)
        

    # -------------------------------
    # Initialize all sub-pages
    # -------------------------------
    def init_sub_pages(self):
        """
        Create QWidget pages, set up their UI, and attach controllers.
        Controllers must be initialized AFTER widget + UI exist.
        """
        # # -------------------------------
        # # Profile page
        # # -------------------------------
        self.profile_page = ProfileWidget(self.student, self.user_info)

        # -------------------------------
        # Current Sched page
        # -------------------------------
        # this page sets up its own ui internally.
        self.current_schedule_page = CurrentScheduleWidget(self.student, self.admin_utils)

        # # already added inside innit
        

        # -------------------------------
        # Register Courses page
        # -------------------------------
        # this page sets up its own ui internally.
        self.register_courses_page = RegisterCoursesWidget(self.student, self.admin_utils, semester=None)
        
        # -------------------------------
        # View Prerequisites page
        # -------------------------------
        self.view_prereqs_page = ViewPrereqsWidget(self.student, self.admin_utils)

        # -------------------------------
        # View Program courses
        # -------------------------------
        # this page sets up its own ui internally.
        self.view_program_plans_page = ViewProgramPlansWidget(self.student, self.admin_utils)

        # # -------------------------------
        # # Transcript courses
        # # -------------------------------
        # this page sets up its own ui internally.
        self.transcript_page = TranscriptWidget(self.student, self.admin_utils)        


    # -------------------------------
    # Switch the stacked widget to the page associated with the clicked button
    # -------------------------------
    def switch_to_page(self, button):
        # Retrieve the mapping info for the clicked button
        info = self.page_mapping.get(button)
        if info:
            # Unpack the tuple into a readable name and the actual QWidget page
            name, page = info
            
            # Set the stacked widget to display the selected page
            self.ui.stackedWidget.setCurrentWidget(page)
            
            # Optional debug: safely print the human-readable name of the page
            print(f"Switched to page: {name}")

    # ------- Cool Logout Functionality -----------
    def fade_and_logout(self):
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer

        # IMPORTANT: Prevent Qt from quitting
        QtWidgets.QApplication.instance().setQuitOnLastWindowClosed(False)

        # Create fade-out animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(350)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # When fade finishes → close → wait → show login
        self.anim.finished.connect(lambda: (
            self.close(),
            QTimer.singleShot(50, self.show_authentication_window)
        ))

        self.anim.start()


    def show_authentication_window(self):
        from login_files.class_authentication_window import AuthenticationWindow
        self.authentication_window = AuthenticationWindow(self.db)
        self.authentication_window.show()


    def update_connection_status(self):
        """ updates the "online" label dynamicly 
        based on whether user is connected to db or not"""
        if is_connected_to_db():
            self.ui.labelStudentStatus.setText("🟢Online") # <----- the label 

        else:
            self.ui.labelStudentStatus.setText("🔴Offline") # <----- the label 


# ------------------------------- MAIN APP -------------------------------
# ------------------------------- MAIN APP (TEST ONLY) -------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities

    # Create pooled DB connection for testing
    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    fake_user_info = (
        2599999,             # user_id ()
        "Test Student",      # name
        "test@example.com",  # email
        "COMP",              # program
        "student",           # state
        "active",            # account_status
        "fake_hash",         # hashed password (unused by dashboard)
    )

    window = StudentDashboard(db, fake_user_info)
    window.show()
    sys.exit(app.exec())
