import sys
from PyQt6.QtWidgets import QApplication

# DB connectivity check
from database_files.cloud_database import is_connected_to_db, get_pooled_connection
from database_files.class_database_uitlities import DatabaseUtilities

from helper_files.shared_utilities import warning


def main():
    # ----------------------------
    # Create the Qt application
    # ----------------------------
    app = QApplication(sys.argv)

    # ----------------------------
    # 1. Check internet / DB availability
    # ----------------------------
    if not is_connected_to_db():
        warning(None,
            "Unable to connect to the cloud database.\n"
            "Please check your internet connection and try again."
        )
        sys.exit(1)

    # ----------------------------
    # 2. Create the pooled DB connection
    # ----------------------------
    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    # --------------------------------------------------------------
    # 3. Import AuthenticationWindow AFTER DB is ready
    # --------------------------------------------------------------
    from login_files.class_authentication_window import AuthenticationWindow

    # ----------------------------
    # 4. Start the authentication UI
    # ----------------------------
    window = AuthenticationWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
