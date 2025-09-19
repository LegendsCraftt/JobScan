from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from model.SQL_logic import build_pkg_content_list


class SQLWorker(QObject):
    msg = pyqtSignal(str)
    finished = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, job_code: int, pkg_code: str):
        super().__init__()
        self.job_code = job_code
        self.pkg_code = pkg_code

    @pyqtSlot()
    def run(self):
        try:
            mainmarks, parts = build_pkg_content_list(self.job_code, self.pkg_code)
            print("[SQLWorker] SQL data fetched successfully")
            for mark in mainmarks:
                self.msg.emit(f'Found: {mark}')

            for part in parts:
                self.msg.emit(f'Found: {part}')

            self.finished.emit(mainmarks, parts)
        except Exception as e:
            self.error.emit(str(e))