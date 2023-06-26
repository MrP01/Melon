"""A collection of widgets and classes for the definition of task display in the UI."""
from PySide6 import QtWidgets
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QIcon, QPainter, QPaintEvent

from melon.todo import Todo

ADD_TASK_EDIT_ROLE = "add-task"
UserRole = Qt.ItemDataRole.UserRole


class OrderableTaskItem(QtWidgets.QListWidgetItem):
    """A subclass of QListWidgetItem that can be sorted according to a few specific rules, i.e. due date."""

    def __lt__(self, other: QtWidgets.QListWidgetItem):
        """This method will by called by QListWidget.sort() to compare items to one another.

        Args:
            other (QListWidgetItem): Argument
        """
        if self.data(Qt.ItemDataRole.EditRole) == ADD_TASK_EDIT_ROLE:
            return False
        elif other.data(Qt.ItemDataRole.EditRole) == ADD_TASK_EDIT_ROLE:
            return True
        mine: Todo = self.data(UserRole)
        theirs: Todo = other.data(UserRole)
        return mine < theirs


class CompletionPushButton(QtWidgets.QPushButton):
    """A push button that only displays a specific icon."""

    def __init__(self, parent: QtWidgets.QWidget):
        """
        Args:
            parent (QWidget): Argument
        """
        super().__init__(parent=parent)
        self.okIcon = QIcon("gui/assets/complete.png")
        self.setFixedSize(34, 34)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Args:
            event (QPaintEvent): Argument
        """
        painter = QPainter(self)
        delta = 2 if self.isDown() else 0
        self.okIcon.paint(painter, QRect(delta, delta, 32, 32))


class TaskOverlayWidget(QtWidgets.QWidget):
    """This is the task overlay widget we put above todos in the list display."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialises the widget and adds the necessary GUI subcomponents."""
        super().__init__(parent)
        self.completionBtn = CompletionPushButton(parent=self)
        self.completionBtn.move(18, 8)
