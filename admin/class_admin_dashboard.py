import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))


from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from admin.class_admin_utilities import AdminUtilities
from admin.class_admin_utilities import admin, db
from database_files.cloud_database import is_connected_to_db

# Subpage UI & Controller imports
from app_ui.admin_ui.ui_admin_dashboard import Ui_AdminDashboard

from app_ui.admin_ui.submenus_ui.ui_profile import Ui_Profile
from admin.submenus.class_profile import ProfileWidget

from app_ui.admin_ui.submenus_ui.ui_all_students import Ui_AllStudents
from admin.submenus.class_all_students import AllStudentsController

from app_ui.admin_ui.submenus_ui.ui_pending_requests import Ui_PendingRequestsWidget
from admin.submenus.class_pending_requests import PendingRequestsController

from app_ui.admin_ui.submenus_ui.ui_manage_courses import Ui_ManageCourses
from admin.submenus.class_manage_courses import ManageCoursesController

from app_ui.admin_ui.submenus_ui.ui_manage_prereq import Ui_ManagePrereqs
from admin.submenus.class_manage_prereqs import ManagePrerequisitesController

from app_ui.admin_ui.submenus_ui.ui_manage_sections import Ui_ManageSections
from admin.submenus.class_manage_sections import ManageSectionsWidget

from admin.submenus.class_manage_faculty import ManageFacultyWidget

from app_ui.admin_ui.submenus_ui.ui_manage_students import Ui_ManageStudents
from admin.submenus.class_manage_students import ManageStudentsController

from admin.submenus.class_program_plans import ProgramPlansWidget


class AdminDashboard(QtWidgets.QMainWindow):
    """
    Main admin dashboard window.
    Handles page switching via a QStackedWidget and initializes all sub-pages.
    """
    
    def __init__(self, db, user_info):
        super().__init__()

        # -------------------------------
        # Main UI setup
        # -------------------------------
        self.ui = Ui_AdminDashboard()
        self.ui.setupUi(self)
        self.db = db
        self.user_info = user_info
        self.user_id, self.name, self.email, self.program, self.state, self.account_status, self.hashed_pw = user_info
        self.admin = AdminUtilities(self.db)
        
        # Displays the name at the top-left side near the pfp
        self.ui.labelAdminName.setText(self.name)

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
        self.ui.stackedWidget.addWidget(self.all_students_page)
        self.ui.stackedWidget.addWidget(self.pending_requests_page)

        self.ui.stackedWidget.addWidget(self.manage_students_page)
        self.ui.stackedWidget.addWidget(self.manage_faculty_controller)

        self.ui.stackedWidget.addWidget(self.manage_courses_page)
        self.ui.stackedWidget.addWidget(self.manage_prereqs_page)
        self.ui.stackedWidget.addWidget(self.manage_sections_page)
        self.ui.stackedWidget.addWidget(self.program_plans_page)
        # Add other pages similarly...


        # -------------------------------
        # 3- Map buttons to their corresponding pages
        # -------------------------------

        # Key: QPushButton object
        # Value: Tuple of (page name string, QWidget page)
        # Using a string here avoids printing emojis/unicode directly from button.text()
        self.page_mapping = {
            self.ui.buttonProfile: ("Profile", self.profile_page),
            self.ui.buttonAllStudents: ("All Students", self.all_students_page),
            self.ui.buttonPendingRequests: ("Pending Requests", self.pending_requests_page),

            self.ui.buttonManageStudents: ("Manage Students", self.manage_students_page),
            self.ui.buttonManageFaculty: ("Manage Faculty", self.manage_faculty_controller),

            self.ui.buttonManageCourses: ("Manage Courses", self.manage_courses_page),
            self.ui.buttonManagePrereqs: ("Manage Prereqs", self.manage_prereqs_page),
            self.ui.buttonManageSections: ("Manage Sections", self.manage_sections_page),
            self.ui.buttonProgramPlans: ("Program Plans", self.program_plans_page)
        }

        
        
        # Connect buttons to page-switching logic... using dicts for faster linkage :)
        for button in self.page_mapping.keys():
            button.clicked.connect(lambda checked, b=button: self.switch_to_page(b))

        # Connect logout button
        self.ui.buttonLogout.clicked.connect(self.fade_and_logout)

        # Show default page (should be profile first)
        self.switch_to_page(self.ui.buttonProfile)


        # EXTRA!
        # Start live DB connection monitor!! Checks if user is connected to database or not
        # i.e., checks if user has internet connection or not
        # then updates status label accordingly
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.update_connection_status)
        self.connection_timer.start(5000)  # check every 5 seconds

        # Force first update instantly
        self.update_connection_status()
                

    # -------------------------------
    # Initialize all sub-pages
    # -------------------------------
    def init_sub_pages(self):
        """
        Create QWidget pages, set up their UI, and attach controllers.
        Controllers must be initialized AFTER widget + UI exist.
        """
        # -------------------------------
        # Profile page
        # -------------------------------

        self.profile_page = ProfileWidget(self.user_info)


        # -------------------------------
        # All Students page
        # -------------------------------
        # Uses direct database_utilities access
        self.all_students_page = QtWidgets.QWidget()
        self.all_students_ui = Ui_AllStudents()
        self.all_students_ui.setupUi(self.all_students_page)

        # نمرر كائن الأدمن (self.admin) للكنترولر
        self.all_students_controller = AllStudentsController(self.all_students_ui, self.admin)

        # -------------------------------
        # Pending Requests page
        # -------------------------------
        self.pending_requests_page = QtWidgets.QWidget()
        self.pending_requests_ui = Ui_PendingRequestsWidget()
        self.pending_requests_ui.setupUi(self.pending_requests_page)
        # Uses direct database_utilities access
        self.pending_requests_controller = PendingRequestsController(self.pending_requests_ui, admin)

        # -------------------------------
        # Manage students page
        # -------------------------------
        self.manage_students_page = QtWidgets.QWidget()
        self.manage_students_ui = Ui_ManageStudents()
        self.manage_students_ui.setupUi(self.manage_students_page)
        # uses direct database access
        self.manage_students_controller = ManageStudentsController(self.manage_students_ui, self.admin)


        # -------------------------------
        # Manage facutly page
        # -------------------------------
        # uses database utils
        self.manage_faculty_controller = ManageFacultyWidget(db)

        # -------------------------------
        # Manage courses
        # -------------------------------
        self.manage_courses_page = QtWidgets.QWidget()
        self.manage_courses_ui = Ui_ManageCourses()
        self.manage_courses_ui.setupUi(self.manage_courses_page)
        # Uses direct database_utilities access
        self.manage_courses_controller = ManageCoursesController(self.manage_courses_ui, self.db)

        # -------------------------------
        # Manage prereqs
        # -------------------------------
        self.manage_prereqs_page = QtWidgets.QWidget()
        self.manage_prereqs_ui = Ui_ManagePrereqs()
        self.manage_prereqs_ui.setupUi(self.manage_prereqs_page)
        # Uses admin_utilities and direct database_utilites
        self.manage_prereqs_controller = ManagePrerequisitesController(self.manage_prereqs_ui, self.admin, self.db)

        # -------------------------------
        # Manage sections
        # -------------------------------
        # # no need for all the extra junk since this page sets up its own ui internally. thanks to salem :)
        self.manage_sections_page = ManageSectionsWidget(admin)


        # -------------------------------
        # Program Plans
        # -------------------------------
        self.program_plans_page = ProgramPlansWidget(admin)

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
        from login_files.class_authentication_window import AuthenticationWindow
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
        """ method to return back to the login/create account screen
        mainly used by the "logout" button when pressed """
        from login_files.class_authentication_window import AuthenticationWindow
        self.authentication_window = AuthenticationWindow()
        self.authentication_window.show()


    def update_connection_status(self):
        """ updates the "online" label dynamicly 
        based on whether user is connected to db or not"""
        if is_connected_to_db():
            self.ui.adminStatus.setText("🟢Online") # <----- the label 

        else:
            self.ui.adminStatus.setText("🔴Offline") # <----- the label 
    


# ------------------------------- MAIN APP -------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    user_id = None
    user_name = None
    user_email = None
    user_program = None
    state = None
    account_status = None
    hashed_pw = None

    user_info = user_id, user_name, user_email, user_program, state, account_status, hashed_pw
    window = AdminDashboard(db, user_info)
    window.show()
    sys.exit(app.exec())
