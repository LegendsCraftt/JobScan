
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from model.email import (has_classic_outlook, compose)

class EmailWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, version, attachment_path: Path, access_token: str|None):
        super().__init__()
        self.version = version
        self.attachment_path = attachment_path
        self.access_token = access_token

    @pyqtSlot()
    def run(self):
        try:
            if self.version == 'old':
                has_old = has_classic_outlook()
                if has_old:
                    ok = compose(version=self.version,
                                 attachment_path=str(self.attachment_path),
                                 access_token=self.access_token)

                    if ok:
                        self.finished.emit("OPEN")
                    else:
                        self.error.emit("ERROR")
                else:
                    self.error.emit("ERROR")

            if self.version == 'new':
                ok = compose(version=self.version,
                             attachment_path=str(self.attachment_path),
                             access_token=self.access_token)
                if ok:
                    self.finished.emit("OPEN")
                else:
                    self.error.emit("ERROR")
        except Exception as e:
            self.error.emit(str(e))