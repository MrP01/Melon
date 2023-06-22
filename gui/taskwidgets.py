from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QIcon, QPainter, QPaintEvent
from PySide6.QtWidgets import QListWidgetItem, QPushButton, QWidget

from melon.todo import Todo

ADD_TASK_EDIT_ROLE = "add-task"
NEW_TASK_TEXT = "An exciting new task!"
UserRole = Qt.ItemDataRole.UserRole


class MyListWidgetItem(QListWidgetItem):
    def __lt__(self, other: QListWidgetItem):
        """
        Args:
            other (QListWidgetItem) : Argument
        """
        if self.data(Qt.ItemDataRole.EditRole) == ADD_TASK_EDIT_ROLE:
            return False
        elif other.data(Qt.ItemDataRole.EditRole) == ADD_TASK_EDIT_ROLE:
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


class CompletionPushButton(QPushButton):
    def __init__(self, parent: QWidget):
        """
        Args:
            parent (QWidget) : Argument
        """
        super().__init__(parent=parent)
        self.okIcon = QIcon("gui/assets/complete.png")
        self.setFixedSize(34, 34)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Args:
            event (QPaintEvent) : Argument

        """
        painter = QPainter(self)
        delta = 2 if self.isDown() else 0
        self.okIcon.paint(painter, QRect(delta, delta, 32, 32))


class TaskOverlayWidget(QWidget):
    pass
