# --- update_ui.py (UpdateUI only; worker is fine) ---
from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, url: str, dest_path: str, downloader_func):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.downloader_func = downloader_func
    def run(self):
        try:
            self.downloader_func(self.url, self.dest_path, self.progress.emit)
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

class UpdateUI(QDialog):
    def __init__(self, parent=None, title='JobScan Update'):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(300, 200)

        self._downloaded_path = None
        self._on_restart_now = None
        self._on_restart_later = None

        self.label = QLabel("Downloading update...")
        self.bar = QProgressBar(); self.bar.setRange(0, 100)

        self.restart_now = QPushButton("Restart Now")
        self.restart_now.clicked.connect(self._restart_now_clicked)
        self.restart_later = QPushButton("Later")
        self.restart_later.clicked.connect(self._restart_later_clicked)

        for b in (self.restart_now, self.restart_later):
            b.setEnabled(False)

        row = QHBoxLayout(); row.addWidget(self.restart_now); row.addWidget(self.restart_later)
        layout = QVBoxLayout(self)                 # << attach to self
        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        layout.addLayout(row)

    def bind_worker(self, worker: DownloadWorker):
        self._thread = QThread(self)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.progress.connect(self.bar.setValue)
        worker.finished.connect(self._on_finished)
        worker.error.connect(self._on_error)
        self.finished.connect(lambda _: self._thread.quit())
        self._thread.start()

    # keep your public setter names
    def on_restart_now_clicked(self, cb):     self._on_restart_now = cb
    def on_restart_later_clicked(self, cb):   self._on_restart_later = cb

    def _on_finished(self, path: str):
        self._downloaded_path = path
        self.label.setText("Update downloaded. Restart now?")
        self.restart_now.setEnabled(True); self.restart_later.setEnabled(True)

    def _on_error(self, msg: str):
        self.label.setText(f"Download Failed: {msg}")
        self.restart_later.setText("Close")
        self.restart_now.setEnabled(False); self.restart_later.setEnabled(True)

    def _restart_now_clicked(self):
        if self._on_restart_now and self._downloaded_path:
            self._on_restart_now(self._downloaded_path)
        self.accept()

    def _restart_later_clicked(self):
        if self._on_restart_later and self._downloaded_path:
            self._on_restart_later(self._downloaded_path)
        self.accept()

