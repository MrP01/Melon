from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeyEvent
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QLineEdit, QListWidgetItem, QWidget

from melon.melon import TodoList
from melon.todo import Todo

from .calendarlist import CalendarListView
from .tasklist import TaskListView, UserRole


class GuiTodoList(TodoList):
    def __init__(self) -> None:
        super().__init__()
        self.tasklistView: TaskListView | None = None

    def addOrUpdateTask(self, todo: Todo):
        assert self.tasklistView is not None
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
        self.tasklistView.addTask(todo)


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
        self.searchWidget = QLineEdit()
        self.searchWidget.setPlaceholderText("Search tasks...")
        self.messageLabel = QLabel(self)
        self.messageLabel.setHidden(True)
        self.messageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QGridLayout(self)
        layout.addWidget(self.messageLabel, 0, 1, 1, 2)
        # layout.addWidget(self.searchWidget, 0, 1, 1, 2)
        layout.addWidget(self.calendarlistView, 1, 1)
        layout.addWidget(self.tasklistView, 1, 2)
        self.setLayout(layout)

    def start(self):
        self.todolist.startup()
        self.tasklistView.sortItems()
        self.calendarlistView.populate(self.todolist.calendars.values())
        # QTimer.singleShot(200, self.sync)

    def sync(self):
        self.showInfoMessage("Syncing...")
        QApplication.processEvents()
        self.todolist.syncAll()
        self.tasklistView.sortItems()
        self.hideMessage()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.todolist.store()
        return super().closeEvent(event)

    def calendarListClicked(self, item: QListWidgetItem):
        userData = item.data(Qt.ItemDataRole.UserRole)
        if userData and userData["is-special"] and userData["specialty"] == "all":
            self.tasklistView.clearCalendarFilter()
        else:
            self.tasklistView.setCalendarFilter(item.text())

    def keyPressEvent(self, event: QKeyEvent):
        # print("Key Event", event)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_W:
                self.close()
            elif event.key() == Qt.Key.Key_S:
                self.sync()
            elif event.key() == Qt.Key.Key_H:
                self.calendarlistView.setCurrentRow(0)
            elif event.key() == Qt.Key.Key_Plus:
                self.tasklistView.addEmptyTask()
        # if Qt.Key.Key_A <= event.key() <= Qt.Key.Key_Z:
        #     self.searchWidget.setFocus()
        return super().keyPressEvent(event)

    def showInfoMessage(self, msg: str):
        self.messageLabel.setText(msg)
        self.messageLabel.setHidden(False)

    def hideMessage(self):
        self.messageLabel.setHidden(True)
