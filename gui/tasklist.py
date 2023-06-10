from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import Todo

UserRole = Qt.ItemDataRole.UserRole


class TaskItemEditorFactory(QItemEditorFactory):
    def createEditor(self, userType: int, parent: QWidget) -> QWidget:
        edit = QLineEdit(parent)
        edit.setAlignment(Qt.AlignmentFlag.AlignTop)
        edit.setContentsMargins(14, 2, 2, 4)
        return edit


class TaskItemDelegate(QItemDelegate):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.setItemEditorFactory(TaskItemEditorFactory())

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        todo = index.data(UserRole)
        rect: QRect = option.rect
        originalPen = painter.pen()
        originalFont = painter.font()

        path = QPainterPath()
        path.addRoundedRect(rect.marginsRemoved(QMargins(2, 2, 2, 4)), 6, 6)
        painter.setPen(QPen(QColor(0, 255, 0, 150)))
        painter.fillPath(path, QColor(200, 200, 200, 30))
        if option.state & QStyle.StateFlag.State_Selected:
            path = QPainterPath()
            path.addRoundedRect(QRect(rect.x() + 2, rect.y() + 2, 8, 44), 6, 6)
            painter.fillPath(path, QColor(0, 170, 255, 200))

        path = QPainterPath()
        path.addRoundedRect(QRect(rect.x() + 14, rect.y() + 25, len(todo.calendarName) * 8 + 12, 16), 10, 10)
        painter.drawPath(path)
        painter.setFont(QFont("Monospace", 9))
        painter.drawText(rect.translated(22, 26), todo.calendarName)

        painter.setPen(originalPen)
        painter.setFont(originalFont)
        painter.drawText(rect.translated(18, 3), index.data())

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(100, 50)


class TaskListView(QListWidget):
    def __init__(self):
        super().__init__()
        self.setItemDelegate(TaskItemDelegate())
        self.setDragEnabled(True)
        self.itemChanged.connect(self.onItemChange)

    def populate(self, tasks: list[Todo]):
        self.clear()
        for task in tasks:
            item = QListWidgetItem(task.summary)
            item.setData(UserRole, task)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            self.addItem(item)

    def setCalendarFilter(self, calendarName):
        for i in range(self.count()):
            item = self.item(i)
            if calendarName is not None:
                item.setHidden(item.data(UserRole).calendarName != calendarName)
            else:
                item.setHidden(False)

    def clearCalendarFilter(self):
        for i in range(self.count()):
            self.item(i).setHidden(False)

    def onItemChange(self, item: QListWidgetItem):
        todo: Todo = item.data(UserRole)
        todo.summary = item.text()
        print("Item Changed", item.text(), todo)
        todo.save()
        print("... saved!")
