#!/usr/bin/env python
"""Main entry file for the Graphical User Interface."""
import logging
import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from gui.mainwindow import MainWindow

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.buildUI()
    window.start()
    window.show()
    screenSize: QSize = app.primaryScreen().availableSize()
    window.resize(screenSize.width() // 2, screenSize.height())
    window.move(screenSize.width() // 2, 0)
    sys.exit(app.exec())
