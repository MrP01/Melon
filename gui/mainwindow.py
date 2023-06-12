from PySide6.QtWidgets import *

from melon.tasks import TodoList

from .calendarlist import *
from .tasklist import *


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.todolist = TodoList()
        self.setWindowTitle("Melon UI")
        self.todolist.startup()
        QTimer.singleShot(200, self.todolist.sync)

    def buildUI(self):
        self.tasklist = TaskListView(self.todolist)
        self.tasklist.populate(self.todolist.tasks)

        calendarList = CalendarList()
        calendarList.populate(self.todolist.calendars.values())
        calendarList.currentItemChanged.connect(self.calendarListClicked)

        layout = QGridLayout(self)
        layout.addWidget(calendarList, 1, 1)
        layout.addWidget(self.tasklist, 1, 2)
        self.setLayout(layout)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.todolist.store()
        return super().closeEvent(event)

    def calendarListClicked(self, item):
        userData = item.data(Qt.ItemDataRole.UserRole)
        if userData and userData["is-special"] and userData["specialty"] == "all":
            self.tasklist.clearCalendarFilter()
        else:
            self.tasklist.setCalendarFilter(item.text())

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
        return super().keyPressEvent(event)
