from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class AboutWindow(QDialog):
    def __init__(self, style: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About JobScan")
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("JobScan Utility")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "JobScan helps streamline retrieval of all production files tied to a specific job/package.\n\n"
            "Usage:\n"
            "1. Enter the Job Code and Package Name.\n"
            "2. Select file types to include (Parts, Assemblies, NC, DXF, ENC).\n"
            "3. Set the output path (optional).\n"
            "4. Press 'Scan' to collect matching files into a structured export.\n\n"
            "Extras:\n"
            "- Enable 'Attach to Email' to prep the package for Outlook.\n"
            "- Overwrite existing exports if desired.\n"
            "- Theme toggle + settings persistence supported.\n\n"

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

