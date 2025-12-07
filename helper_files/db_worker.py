from PyQt6.QtCore import QThread, pyqtSignal

class DbWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            result = self.fn()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(e)
