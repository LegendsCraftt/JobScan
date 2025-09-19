from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QCheckBox

from custom_widgets.separator import h_line

class PreferencesPanel(QFrame):
    def __init__(self, parent=None, width=280):
        super().__init__(parent)
        self._panel_width = width
        self.setObjectName("sidePanel")
        self.setFixedWidth(self._panel_width)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.separator = h_line()

        # Content
        menu_layout = QVBoxLayout(self)
        menu_layout.setContentsMargins(16, 16, 16, 16)
        menu_layout.setSpacing(12)

        title_layout = QHBoxLayout()

        title = QLabel("Preferences")
        title.setObjectName("sidePanelTitle")

        menu_button = QPushButton("☰")
        menu_button.clicked.connect(self.toggle)
        menu_button.setObjectName("sidePanelButton")

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(menu_button)

        content_layout = QVBoxLayout()
        content_layout.addWidget(self.separator)

        inner_layout = QVBoxLayout()
        outlook_option_layout = QHBoxLayout()

        self.outlook_option_title = QLabel("Outlook Options—")
        self.outlook_option_title.setObjectName("sidePanelSubTitle")
        inner_layout.addWidget(self.outlook_option_title)

        self.outlook_new_check = QCheckBox("New Outlook (Browser)")
        self.outlook_old_check = QCheckBox("Old Outlook")

        outlook_option_layout.addWidget(self.outlook_new_check)
        outlook_option_layout.addWidget(self.outlook_old_check)
        inner_layout.addLayout(outlook_option_layout)

        self.overwrite_title = QLabel('Overwrite Existing Files—')
        self.overwrite_title.setObjectName("sidePanelSubTitle")

        self.overwrite_check = QCheckBox('Overwrite')

        inner_layout.addSpacing(12)
        inner_layout.addWidget(self.overwrite_title)
        inner_layout.addWidget(self.overwrite_check)


        content_layout.addLayout(inner_layout)

        content_layout.addStretch()

        menu_layout.addLayout(title_layout)

        menu_layout.addLayout(content_layout)


        # Scrim overlay to catch outside clicks
        self._overlay = QWidget(parent)
        self._overlay.setObjectName("scrimOverlay")
        self._overlay.hide()
        self._overlay.installEventFilter(self)

        # Anim
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hide()

    # --- public API ---
    def toggle(self):
        if self.isVisible():
            self.closePanel()
        else:
            self.openPanel()

    def openPanel(self):
        p = self.parentWidget()
        if not p:
            return
        self._positionOverlay()
        self._overlay.show()
        self.show()


        self._overlay.raise_()
        self.raise_()

        start = QRect(p.width(), 0, self._panel_width, p.height())
        end = QRect(p.width() - self._panel_width, 0, self._panel_width, p.height())
        self.setGeometry(start)
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def closePanel(self):
        p = self.parentWidget()
        if not p:
            return
        start = QRect(self.geometry())
        end   = QRect(p.width(), 0, self._panel_width, p.height())
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.finished.connect(self._afterCloseOnce)
        self._anim.start()

    def _afterCloseOnce(self):
        try:
            self._anim.finished.disconnect(self._afterCloseOnce)
        except Exception:
            pass
        self.hide()
        self._overlay.hide()

    # Keep aligned on parent resize
    def resizeWithParent(self):
        p = self.parentWidget()
        if not p:
            return
        self._positionOverlay()
        if self.isVisible():
            self.setGeometry(p.width() - self._panel_width, 0, self._panel_width, p.height())

    def _positionOverlay(self):
        p = self.parentWidget()
        if p:
            self._overlay.setGeometry(0, 0, p.width(), p.height())

    def eventFilter(self, obj, ev):
        if obj is self._overlay and ev.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            self.closePanel()
            return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.closePanel()
        else:
            super().keyPressEvent(e)
