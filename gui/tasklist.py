import caldav
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import Todo, TodoList

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
        if todo is None:
            return

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


class MyListWidgetItem(QListWidgetItem):
    def __lt__(self, other: QListWidgetItem):
        if self.data(Qt.ItemDataRole.EditRole) == "add-task":
            return False
        elif other.data(Qt.ItemDataRole.EditRole) == "add-task":
            return True
        if self.data(UserRole).summary == "An exciting new task!":
            return False
        return self.data(UserRole).summary < other.data(UserRole).summary


class TaskListView(QListWidget):
    def __init__(self, todolist: TodoList):
        super().__init__()
        self.todolist = todolist
        self.setItemDelegate(TaskItemDelegate())
        self.setDragEnabled(True)
        self.itemChanged.connect(self.onItemChange)
        self._currentCalendarName = None

    def createListItemFromTask(self, task: Todo):
        item = MyListWidgetItem(task.summary)
        item.setData(UserRole, task)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
        return item

    def populate(self, tasks: list[Todo]):
        self.clear()
        for task in tasks:
            self.addItem(self.createListItemFromTask(task))
        self.addAddButton()
        self.sortItems()

    def addAddButton(self):
        self._addTaskItem = MyListWidgetItem("Add Task")
        self._addTaskItem.setData(Qt.ItemDataRole.EditRole, "add-task")
        self.addItem(self._addTaskItem)
        addButton = QPushButton(QIcon.fromTheme("list-add"), "Add Task")
        addButton.clicked.connect(self.onAddTask)
        self.setItemWidget(self._addTaskItem, addButton)

    def setCalendarFilter(self, calendarName):
        for i in range(self.count()):
            item = self.item(i)
            if calendarName is not None and item.data(UserRole) is not None:
                item.setHidden(item.data(UserRole).calendarName != calendarName)
            else:
                item.setHidden(False)
        self._currentCalendarName = calendarName

    def clearCalendarFilter(self):
        for i in range(self.count()):
            self.item(i).setHidden(False)
        self._currentCalendarName = None

    def onItemChange(self, item: QListWidgetItem):
        todo: Todo = item.data(UserRole)
        todo.summary = item.text()
        todo.save()
        print("... saved!")

    def onAddTask(self):
        if self._currentCalendarName is None:
            print("Please select a calendar first!")
            return
        calendar = self.todolist.calendars[self._currentCalendarName]
        todo = Todo(
            caldav.Todo(
                calendar.client,
                data=calendar._use_or_create_ics("SUMMARY:An exciting new task!", objtype="VTODO"),
                parent=calendar,
            ),
            calendarName=calendar.name,
        )
        newItem = self.createListItemFromTask(todo)
        self.addItem(newItem)
        self.sortItems()
        self.editItem(newItem)
