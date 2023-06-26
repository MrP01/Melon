"""This module defines the task list view widget."""
import logging
import re

import dateparser.search
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeyEvent, QMouseEvent

from melon.melon import Melon
from melon.todo import Todo

from .taskitemdelegate import TaskItemDelegate
from .taskwidgets import OrderableTaskItem, TaskOverlayWidget, UserRole


class TaskListView(QtWidgets.QListWidget):
    """Subclass of QListWidget containing tasks."""

    def __init__(self, melon: Melon):
        """Initialise the task list, a QListWidget displaying tasks in a list, using data from `melon`.

        Args:
            melon (Melon): The Melon instance to obtain data from
        """
        super().__init__()
        self.melon = melon
        delegate = TaskItemDelegate(self)
        self.setItemDelegate(delegate)
        delegate.editorDestroyed.connect(self.delegateEditorDestroyed)
        self.setDragEnabled(True)
        self.itemChanged.connect(self.onItemChange)
        self._currentCalendarName = None
        self.addAddButton()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        Args:
            event (QMouseEvent): Argument
        """
        item = self.itemAt(event.position().toPoint())
        self.removeItemWidget(item)
        self.editItem(item)

    def addTask(self, task: Todo) -> OrderableTaskItem:
        """
        Args:
            task (Todo): Argument

        Returns:
            (MyListWidgetItem):
        """
        item = OrderableTaskItem(task.summary)
        item.setData(UserRole, task)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
        self.addItem(item)
        self.attachTaskWidget(item)
        return item

    def attachTaskWidget(self, item):
        """
        Args:
            item: Argument
        """
        widget = TaskOverlayWidget(parent=self)
        widget.completionBtn.clicked.connect(lambda: self.completeTask(item))
        self.setItemWidget(item, widget)

    def completeTask(self, item: QtWidgets.QListWidgetItem):
        """
        Args:
            item (QListWidgetItem): Argument
        """
        task: Todo = item.data(UserRole)
        task.complete()
        self.takeItem(self.row(item))

    def addAddButton(self):
        """
        Args:
        """
        self._addTaskItem = OrderableTaskItem("Add Task")
        self._addTaskItem.setData(Qt.ItemDataRole.EditRole, "add-task")
        self.addItem(self._addTaskItem)
        addButton = QtWidgets.QPushButton(QIcon.fromTheme("list-add"), "Add Task")
        addButton.clicked.connect(self.addEmptyTask)
        self.setItemWidget(self._addTaskItem, addButton)

    def setCalendarFilter(self, calendarName):
        """
        Args:
            calendarName: Argument
        """
        for i in range(self.count()):
            item = self.item(i)
            if calendarName is not None and item.data(UserRole) is not None:
                item.setHidden(item.data(UserRole).calendarName != calendarName)
            else:
                item.setHidden(False)
        self._currentCalendarName = calendarName

    def clearCalendarFilter(self):
        """
        Args:
        """
        for i in range(self.count()):
            self.item(i).setHidden(False)
        self._currentCalendarName = None

    def onItemChange(self, item: QtWidgets.QListWidgetItem):
        """
        Args:
            item (QListWidgetItem): Argument
        """
        todo: Todo = item.data(UserRole)
        if todo.calendarName is None:
            raise ValueError("The item's associated todo does not have a calendar.")

        text = item.text()
        if "clear" in text:
            todo.dueDate = None
            text = text.replace("clear", "")
        else:
            extractedDateTime = dateparser.search.search_dates(text)
            if extractedDateTime:
                token, stamp = extractedDateTime[0]
                if re.search(r"\d", token):
                    todo.dueDate = stamp
                else:
                    todo.dueDate = stamp.date()
        todo.summary = text.strip()
        todo.save()
        logging.info("... saved!")
        self.melon.syncCalendar(self.melon.calendars[todo.calendarName])
        logging.debug("... and synced!")

    def addEmptyTask(self):
        """
        Args:
        """
        if self._currentCalendarName is None:
            print("Please select a calendar first!")
            return
        calendar = self.melon.calendars[self._currentCalendarName]
        todo = calendar.createTodo()
        item = self.addTask(todo)
        self.sortItems()
        self.removeItemWidget(item)
        self.scrollToItem(item)
        self.editItem(item)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Args:
            event (QKeyEvent): Argument
        """
        # if event.key() == Qt.Key.Key_Plus:
        #     self.addEmptyTask()
        return super().keyPressEvent(event)

    def delegateEditorDestroyed(self, index):
        """
        Args:
            index: Argument
        """
        if self.itemWidget(self.itemFromIndex(index)) is None:
            self.attachTaskWidget(self.itemFromIndex(index))
