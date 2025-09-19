from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from pathlib import Path
from model.main_logic import sort_to_dirs
import traceback


class ScanWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, targets: list[str], output_root: Path, files: dict, overwrite: bool = False):
        super().__init__()
        self.targets = targets
        self.output_root = Path(output_root)
        self.files = files
        self.overwrite = overwrite

    @pyqtSlot()
    def run(self):
        try:
            print("[ScanWorker] Starting sort_to_dirs...")
            sort_to_dirs(self.targets, self.files, self.output_root, self.overwrite)
            print("[ScanWorker] Sort complete")
            self.finished.emit("Scan Complete")
        except Exception as e:
            print(traceback.format_exc())
            self.error.emit(str(e))
