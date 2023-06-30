#!/usr/bin/env python
"""Main entry file for the Graphical User Interface."""
import cProfile
import logging
import pstats
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QSize

from melongui.mainwindow import MainWindow

logging.basicConfig(level=logging.INFO)


def main():
    """Starts the Graphical User Interface"""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Melon")
    window = MainWindow()
    window.buildUI()
    window.start()
    window.show()
    screenSize: QSize = app.primaryScreen().availableSize()
    window.resize(screenSize.width() // 2, screenSize.height())
    window.move(screenSize.width() // 2, 0)
    sys.exit(app.exec())


if __name__ == "__main__":
    if "--profile" in sys.argv:
        cProfile.run("main()", sort=pstats.SortKey.CUMULATIVE)
    else:
        main()
