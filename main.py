#!/usr/bin/env python
import logging
import sys

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from gui.mainwindow import *

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.buildUI()
    window.show()
    sys.exit(app.exec())
