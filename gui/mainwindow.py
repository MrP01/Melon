from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import TodoList

from .tasklist import *


class LargerListViewDelegate(QItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        return QSize(100, 27)


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

        calendarList = QListWidget()
        calendarList.setItemDelegate(LargerListViewDelegate())
        for calendar in self.todolist.calendars:
            calendarList.addItem(calendar.name)
        calendarList.sortItems()
        policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        policy.setHorizontalStretch(2)
        calendarList.setSizePolicy(policy)
        calendarList.itemClicked.connect(lambda item: self.tasklist.setCalendarFilter(item.text()))

        layout = QGridLayout(self)
        layout.addWidget(calendarList, 1, 1)
        layout.addWidget(self.tasklist, 1, 2)
        self.setLayout(layout)

        self.resize(960, 1080)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
        return super().keyPressEvent(event)
