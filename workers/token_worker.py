from PyQt6.QtCore import (QObject,
                          pyqtSignal,
                          pyqtSlot)

from model.graph_logic import acquire_token

class TokenWorker(QObject):
    """Worker for token acquisition."""
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, interactive: bool):
        super().__init__()
        self.interactive = interactive

    @pyqtSlot()
    def run(self):
        try:
            tok = acquire_token(silent_only=not self.interactive)
            token = (tok or {}).get('access_token', '')
            self.finished.emit(token)

        except Exception as e:
            self.error.emit(str(e))
