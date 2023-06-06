import caldav
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class TaskItemDelegate(QItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        todo = index.data(Qt.ItemDataRole.UserRole)
        rect: QRect = option.rect
        originalPen = painter.pen()
        originalFont = painter.font()

        path = QPainterPath()
        path.addRoundedRect(rect.marginsRemoved(QMargins(2, 2, 2, 2)), 6, 6)
        painter.setPen(QPen(QColor(0, 255, 0, 150)))
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillPath(path, QColor(200, 200, 200, 150))
        else:
            painter.fillPath(path, QColor(200, 200, 200, 50))

        path = QPainterPath()
        path.addRoundedRect(QRect(rect.x() + 4, rect.y() + 25, len(todo.contents["calendar"]) * 8 + 12, 16), 10, 10)
        painter.drawPath(path)
        painter.setFont(QFont("Monospace", 9))
        painter.drawText(rect.translated(12, 26), todo.contents["calendar"])

        painter.setPen(originalPen)
        painter.setFont(originalFont)
        painter.drawText(rect.translated(8, 3), index.data())

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(100, 50)


class TaskListView(QListWidget):
    def __init__(self):
        super().__init__()
        self.setItemDelegate(TaskItemDelegate())

    def populate(self, tasks: list[caldav.Todo]):
        self.clear()
        for task in tasks:
            try:
                item = QListWidgetItem(task.vobject_instance.contents["summary"][0].value)
                todo = task.vobject_instance
            except KeyError:  # when the task is wrapped in a VCalendar object
                item = QListWidgetItem(task.vobject_instance.contents["vtodo"][0].contents["summary"][0].value)
                todo = task.vobject_instance.contents["vtodo"][0]
            item.setData(Qt.ItemDataRole.UserRole, todo)
            self.addItem(item)
