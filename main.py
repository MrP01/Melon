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
    window.start()
    window.show()
    screenSize = app.primaryScreen().availableSize()
    window.resize(screenSize.width() // 2, screenSize.height())
    window.move(screenSize.width() // 2, 0)
    sys.exit(app.exec())
