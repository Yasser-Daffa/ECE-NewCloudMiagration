from PyQt6.QtCore import QThread, pyqtSignal

class DbWorker(QThread):
    """
    Runs a function in a background thread to avoid blocking the UI.
    Emits the function's return value when finished.
    """
    finished = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn  # function to execute (no arguments)

    def run(self):
        try:
            result = self.fn()          # run task in background
            self.finished.emit(result)  # send result back to UI
        except Exception as e:
            self.finished.emit(e)       # send exception if something fails
