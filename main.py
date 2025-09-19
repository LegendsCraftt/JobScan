import sys
import multiprocessing

from PyQt6.QtWidgets import QApplication

from UI.styles_d import style
from UI.ui import MainUI

def main():
    app = QApplication([])
    window = MainUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()