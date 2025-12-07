from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from database_files.cloud_database import attempt_connection_with_retry


class ConnectionRetryDialog(QDialog):
    """
    A simple retry dialog shown when DB is unreachable.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Database Connection Error")
        self.setFixedSize(380, 180)

        self.label = QLabel(
            "Unable to connect to the cloud database.\n"
            "Check your internet and try again."
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 14px;")

        self.label.setStyleSheet("font-size: 14px;")

        self.btn_retry = QPushButton("Retry")
        self.btn_retry.setStyleSheet("padding: 8px; font-size: 14px;")

        self.btn_close = QPushButton("Close App")
        self.btn_close.setStyleSheet("padding: 8px; font-size: 14px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.btn_retry)
        layout.addWidget(self.btn_close)

        self.btn_retry.clicked.connect(self.try_connect)
        self.btn_close.clicked.connect(self.reject)  # Close dialog → return False

        self._connect_success = False

    def try_connect(self):
        self.btn_retry.setEnabled(False)
        self.label.setText("Attempting connection...")

        # Try in a timer so UI updates
        QTimer.singleShot(50, self._attempt)

    def _attempt(self):
        ok = attempt_connection_with_retry(max_attempts=3, delay=1)

        if ok:
            self._connect_success = True
            self.accept()     # Close & return True
        else:
            self.label.setText(
                "Still unable to connect.\n"
                "Please check your connection."
            )
            self.btn_retry.setEnabled(True)

    def connection_successful(self):
        return self._connect_success
