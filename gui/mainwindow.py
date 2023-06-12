from PySide6.QtWidgets import *

from melon.tasks import Todo, TodoList

from .calendarlist import *
from .tasklist import *


class GuiTodoList(TodoList):
    def __init__(self) -> None:
        super().__init__()
        self.tasklistView: TaskListView | None = None

    def addOrUpdateTask(self, todo: Todo):
        if todo.isComplete():
            return
        uid = todo.uid
        assert uid is not None
        for i in range(self.tasklistView.count()):
            data = self.tasklistView.item(i).data(UserRole)
            if uid == getattr(data, "uid", None):
                self.tasklistView.blockSignals(True)
                self.tasklistView.item(i).setText(todo.summary)
                self.tasklistView.item(i).setData(UserRole, todo)
                self.tasklistView.blockSignals(False)
                return
        self.tasklistView.addItem(self.tasklistView.createListItemFromTask(todo))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.todolist = GuiTodoList()
        self.setWindowTitle("Melon UI")

    def buildUI(self):
        self.tasklistView = TaskListView(self.todolist)
        self.todolist.tasklistView = self.tasklistView
        self.calendarlistView = CalendarListView()
        self.calendarlistView.currentItemChanged.connect(self.calendarListClicked)

        layout = QGridLayout(self)
        layout.addWidget(self.calendarlistView, 1, 1)
        layout.addWidget(self.tasklistView, 1, 2)
        self.setLayout(layout)

    def start(self):
        self.todolist.startup()
        self.tasklistView.sortItems()
        self.calendarlistView.populate(self.todolist.calendars.values())
        QTimer.singleShot(200, self.sync)

    def sync(self):
        self.todolist.sync()
        self.tasklistView.sortItems()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.todolist.store()
        return super().closeEvent(event)

    def calendarListClicked(self, item):
        userData = item.data(Qt.ItemDataRole.UserRole)
        if userData and userData["is-special"] and userData["specialty"] == "all":
            self.tasklistView.clearCalendarFilter()
        else:
            self.tasklistView.setCalendarFilter(item.text())

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
        return super().keyPressEvent(event)
