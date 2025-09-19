from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class HelpWindow(QDialog):
    def __init__(self, style: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help JobScan")
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Help")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Need Help?\n\n"
            "Check out the about section in the menu bar.\n\n"
            "Contact the developer:\n"
            "Email:           tylere@metalsfab.com\n"
            "Phone #:      (509)-244-2909 EXT 102\n"
        )
        desc.setWordWrap(True)
        desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(desc)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

        if style == 'dark':
            self.setStyleSheet("""

                QDialog {
                    background-color: #1E1E1E;
                }

                QLabel {
                    font-size: 14px;
                    color: #fff;
                }
                QPushButton {
                    padding: 6px 16px;
                    background-color: #444;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)

        if style == 'light':
            self.setStyleSheet("""

                      QDialog {
                          background-color: #FAFAFA;
                      }

                      QLabel {
                          font-size: 14px;
                          color: #000;
                      }
                      QPushButton {
                          padding: 6px 16px;
                          background-color: rgba(0,0,0,0.1);
                          border-radius: 6px;
                      }
                      QPushButton:hover {
                          background-color: rgba(0,0,0,0.08);
                      }
                  """)

