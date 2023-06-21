from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton

from melon.tasks import Todo, TodoList

from .taskitemdelegate import TaskItemDelegate
from .taskwidgets import NEW_TASK_TEXT, CompletionPushButton, MyListWidgetItem, TaskOverlayWidget, UserRole


class TaskListView(QListWidget):
    def __init__(self, todolist: TodoList):
        super().__init__()
        self.todolist = todolist
        self.setItemDelegate(TaskItemDelegate(self))
        self.setDragEnabled(True)
        self.itemChanged.connect(self.onItemChange)
        self._currentCalendarName = None
        self.addAddButton()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        item = self.itemAt(event.position().toPoint())
        self.removeItemWidget(item)
        self.editItem(item)

    def addTask(self, task: Todo) -> MyListWidgetItem:
        item = MyListWidgetItem(task.summary)
        item.setData(UserRole, task)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
        self.addItem(item)
        self.attachTaskWidget(item)
        return item

    def attachTaskWidget(self, item):
        widget = TaskOverlayWidget(parent=self)
        completionBtn = CompletionPushButton(parent=widget)
        completionBtn.move(18, 8)
        completionBtn.clicked.connect(lambda: self.completeTask(item))
        self.setItemWidget(item, widget)

    def completeTask(self, item: QListWidgetItem):
        task: Todo = item.data(UserRole)
        task.complete()
        self.takeItem(self.row(item))

    def addAddButton(self):
        self._addTaskItem = MyListWidgetItem("Add Task")
        self._addTaskItem.setData(Qt.ItemDataRole.EditRole, "add-task")
        self.addItem(self._addTaskItem)
        addButton = QPushButton(QIcon.fromTheme("list-add"), "Add Task")
        addButton.clicked.connect(self.addEmptyTask)
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

    def addEmptyTask(self):
        if self._currentCalendarName is None:
            print("Please select a calendar first!")
            return
        calendar = self.todolist.calendars[self._currentCalendarName]
        todo = calendar.createTodo(NEW_TASK_TEXT)
        item = self.addTask(todo)
        self.sortItems()
        self.removeItemWidget(item)
        self.editItem(item)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Plus:
            self.addEmptyTask()
        return super().keyPressEvent(event)

    def delegateEditorDestroyed(self, index):
        if self.itemWidget(self.itemFromIndex(index)) is None:
            self.attachTaskWidget(self.itemFromIndex(index))
