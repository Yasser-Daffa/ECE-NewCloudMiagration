import sys
from PyQt6.QtWidgets import QApplication

# DB connectivity check
from database_files.cloud_database import is_connected_to_db

from helper_files.shared_utilities import warning


def main():
    # ----------------------------
    # Create the Qt application
    # ----------------------------
    app = QApplication(sys.argv)

    # ----------------------------
    # 1. Check database connection
    # ----------------------------
    if not is_connected_to_db():
        warning(None,
            "Unable to connect to the cloud database.\n"
            "Please check your internet connection and try again."
        )
        sys.exit(1)

    # --------------------------------------------------------------
    # 2. Only NOW import AuthenticationWindow (safe after check)
    # --------------------------------------------------------------
    from login_files.class_authentication_window import AuthenticationWindow

    # ----------------------------
    # 3. Start the authentication UI
    # ----------------------------
    window = AuthenticationWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
