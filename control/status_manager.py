from PyQt6.QtCore import QTimer


class StatusManager:
    def __init__(self, label, get_base_status_callable, timeout_ms = 5000):
        self.label = label
        self.get_base_status = get_base_status_callable
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._revert)
        self._last_transient = None
        self.set_base()

    def set_base(self):
        self._last_transient = None
        self.label.setText(self.get_base_status())

    def show(self, msg: str, auto_revert=True):
        self._last_transient = msg
        self.label.setText(msg)
        if auto_revert:
            self.timer.start(self.timer.interval() or 5000)

    def force(self, msg):
        self.timer.stop()
        self._last_transient = None
        self.label.setText(msg)

    def input_changed(self):
        if not self.timer.isActive():
            self.set_base()

    def _revert(self):
        self.set_base()