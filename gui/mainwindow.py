from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import TodoList

from .tasklist import *


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.todolist = TodoList()
        self.setWindowTitle("Melon UI")

        # self.todolist.connect()
        # self.todolist.fetch()
        # self.todolist.store()
        self.todolist.load()

    def buildUI(self):
        self.tasklist = TaskListView()
        self.tasklist.populate(self.todolist.tasks)

        layout = QGridLayout(self)
        layout.addWidget(self.tasklist, 1, 1)
        self.setLayout(layout)

        self.resize(960, 1080)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
        return super().keyPressEvent(event)
