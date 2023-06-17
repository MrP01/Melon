import datetime

import caldav
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import Todo, TodoList

UserRole = Qt.ItemDataRole.UserRole
ONE_DAY = datetime.timedelta(days=1)
NEW_TASK_TEXT = "An exciting new task!"


class TaskItemEditorFactory(QItemEditorFactory):
    def createEditor(self, userType: int, parent: QWidget) -> QWidget:
        edit = QLineEdit(parent)
        edit.setAlignment(Qt.AlignmentFlag.AlignTop)
        edit.setContentsMargins(18 + 32 + 10, 2, 2, 4)
        return edit


class CompletionPushButton(QPushButton):
    def __init__(self, parent: QObject):
        super().__init__(parent=parent)
        self.okIcon = QIcon("gui/assets/complete.png")
        self.setFixedSize(34, 34)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        delta = 2 if self.isDown() else 0
        self.okIcon.paint(painter, QRect(delta, delta, 32, 32))


class TaskItemDelegate(QItemDelegate):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.setItemEditorFactory(TaskItemEditorFactory())

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        todo: Todo = index.data(UserRole)
        if todo is None:
            return

        rect: QRect = option.rect
        painter.save()
        painter.drawText(rect.translated(18 + 32 + 14, 3), todo.summary)

        dueDate = todo.dueDate
        if dueDate:
            text = dueDate.strftime("%d.%m.%Y")
            today = datetime.date.today()
            if dueDate.date() == today:
                text = "today"
            elif dueDate.date() == today - ONE_DAY:
                text = "yesterday"
            elif dueDate.date() == today + ONE_DAY:
                text = "tomorrow"
            painter.setPen(QPen(QColor(255, 100, 100) if dueDate.date() < today else QColor(150, 150, 150)))
            if dueDate.time() != datetime.time():
                text += ", " + dueDate.strftime("%H:%M")
            painter.drawText(rect.translated(-10, 3), text, Qt.AlignmentFlag.AlignRight)

        path = QPainterPath()
        path.addRoundedRect(rect.marginsRemoved(QMargins(2, 2, 2, 4)), 6, 6)
        painter.setPen(QPen(QColor(0, 255, 0, 150)))
        painter.fillPath(path, QColor(200, 200, 200, 30))
        if option.state & QStyle.StateFlag.State_Selected:
            path = QPainterPath()
            path.addRoundedRect(QRect(rect.x() + 2, rect.y() + 2, 8, 44), 6, 6)
            painter.fillPath(path, QColor(33, 150, 243, 200))

        path = QPainterPath()
        path.addRoundedRect(QRect(rect.x() + 32 + 14 + 14, rect.y() + 25, len(todo.calendarName) * 8 + 12, 16), 10, 10)
        painter.drawPath(path)
        painter.setFont(QFont("Monospace", 9))
        painter.drawText(rect.translated(32 + 14 + 22, 26), todo.calendarName)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(100, 50)


class MyListWidgetItem(QListWidgetItem):
    def __lt__(self, other: QListWidgetItem):
        if self.data(Qt.ItemDataRole.EditRole) == "add-task":
            return False
        elif other.data(Qt.ItemDataRole.EditRole) == "add-task":
            return True
        mine: Todo = self.data(UserRole)
        theirs: Todo = other.data(UserRole)
        if mine.summary == NEW_TASK_TEXT:
            return False
        if theirs.summary == NEW_TASK_TEXT:
            return True
        if mine.dueDate is None and theirs.dueDate is not None:
            return False
        if theirs.dueDate is None and mine.dueDate is not None:
            return True
        return (mine.dueDate, mine.summary) < (theirs.dueDate, theirs.summary)


class TaskListView(QListWidget):
    def __init__(self, todolist: TodoList):
        super().__init__()
        self.todolist = todolist
        self.setItemDelegate(TaskItemDelegate())
        self.setDragEnabled(True)
        self.itemChanged.connect(self.onItemChange)
        self._currentCalendarName = None
        self.addAddButton()

    def createListItemFromTask(self, task: Todo):
        item = MyListWidgetItem(task.summary)
        item.setData(UserRole, task)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
        widget = QWidget(self)
        completionBtn = CompletionPushButton(parent=widget)
        completionBtn.move(18, 8)
        return item, widget

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
        self.todolist.syncCalendar(self.todolist.calendars[todo.calendarName])
        print("... and synced!")

    def onAddTask(self):
        if self._currentCalendarName is None:
            print("Please select a calendar first!")
            return
        calendar = self.todolist.calendars[self._currentCalendarName]
        todo = Todo(
            caldav.Todo(
                calendar.client,
                data=calendar._use_or_create_ics(f"SUMMARY:{NEW_TASK_TEXT}", objtype="VTODO"),
                parent=calendar,
            ),
            calendarName=calendar.name,
        )
        newItem = self.createListItemFromTask(todo)
        self.addItem(newItem)
        self.sortItems()
        self.editItem(newItem)
