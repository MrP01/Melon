import caldav
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class TaskItemDelegate(QItemDelegate):
    def drawDisplay(self, painter: QPainter, option: QStyleOptionViewItem, rect: QRect, text: str) -> None:
        return super().drawDisplay(painter, option, rect, text)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        return QSize(100, 50)


class TaskListView(QListWidget):
    def __init__(self):
        super().__init__()
        self.setItemDelegate(TaskItemDelegate())

    def populate(self, tasks: list[caldav.Todo]):
        self.clear()
        for task in tasks:
            try:
                self.addItem(task.vobject_instance.contents["summary"][0].value)
            except KeyError:  # when the task is wrapped in a VCalendar object
                self.addItem(task.vobject_instance.contents["vtodo"][0].contents["summary"][0].value)
