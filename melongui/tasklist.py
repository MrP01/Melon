"""This module defines the task list view widget."""
import logging
import re

import dateparser.search
from PySide6 import QtWidgets
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QIcon, QKeyEvent, QMouseEvent

from melon.melon import Melon
from melon.todo import Todo
from melongui.contextmenu import TaskContextMenu

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
        self.setVerticalScrollMode(QtWidgets.QListWidget.ScrollMode.ScrollPerPixel)
        self.itemChanged.connect(self.onItemChange)
        self._currentCalendarName = None
        self.addAddButton()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)

    def openContextMenu(self, point: QPoint):
        item = self.itemAt(point)
        todo: Todo = item.data(UserRole)
        menu = TaskContextMenu(todo)
        menu.buildUI()
        # menu.dueDateChanged.connect(self.update)
        position = self.mapToGlobal(point)
        position.setX(position.x() - 200)
        menu.exec(position)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handles mouse double click

        Args:
            event (QMouseEvent): Argument
        """
        item = self.itemAt(event.position().toPoint())
        self.removeItemWidget(item)
        self.editItem(item)

    def addTask(self, task: Todo) -> OrderableTaskItem:
        """Adds a Todo to the list

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
        """For a given ListWidgetItem, attaches a task widget

        Args:
            item: Argument
        """
        widget = TaskOverlayWidget(parent=self)
        widget.completionBtn.clicked.connect(lambda: self.completeTask(item))
        self.setItemWidget(item, widget)

    def completeTask(self, item: QtWidgets.QListWidgetItem):
        """Completes the task associated with the given item.

        Args:
            item (QListWidgetItem): Argument
        """
        task: Todo = item.data(UserRole)
        task.complete()
        self.takeItem(self.row(item))

    def addAddButton(self):
        """Adds the task creation button at the bottom of the list."""
        self._addTaskItem = OrderableTaskItem("Add Task")
        self._addTaskItem.setData(Qt.ItemDataRole.EditRole, "add-task")
        self.addItem(self._addTaskItem)
        addButton = QtWidgets.QPushButton(QIcon.fromTheme("list-add"), "Add Task")
        addButton.clicked.connect(self.addEmptyTask)
        self.setItemWidget(self._addTaskItem, addButton)

    def setCalendarFilter(self, calendarName):
        """Only shows tasks for the given calendar.

        Args:
            calendarName: Argument
        """
        for i in range(self.count()):
            item = self.item(i)
            if calendarName is not None and item.data(UserRole) is not None:
                item.setHidden(item.data(UserRole).calendarName != calendarName)
            else:
                item.setHidden(False)
        self.sortItems()
        self._currentCalendarName = calendarName

    def clearCalendarFilter(self):
        """Clears the calendar filter, hence shows all tasks"""
        for i in range(self.count()):
            self.item(i).setHidden(False)
        self._currentCalendarName = None

    def onItemChange(self, item: QtWidgets.QListWidgetItem):
        """Called when an item's value changes. Handles saving of the underlying object.

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
        """Add an empty task to the bottom for editing and saving later."""
        if self._currentCalendarName is None:
            logging.warning("Please select a calendar first!")
            return
        calendar = self.melon.calendars[self._currentCalendarName]
        todo = calendar.createTodo()
        item = self.addTask(todo)
        self.sortItems()
        self.removeItemWidget(item)
        self.scrollToItem(item)
        self.editItem(item)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handles keypresses.

        Args:
            event (QKeyEvent): Argument
        """
        return super().keyPressEvent(event)

    def delegateEditorDestroyed(self, index):
        """When the editor is destroyed, re-attach the item widget

        Args:
            index: Argument
        """
        if self.itemWidget(self.itemFromIndex(index)) is None:
            self.attachTaskWidget(self.itemFromIndex(index))
