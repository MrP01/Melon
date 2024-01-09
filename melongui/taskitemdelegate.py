"""This module defines how tasks should be rendered in the GUI."""
import datetime
from typing import Callable

import dateparser.search
from PySide6 import QtWidgets
from PySide6.QtCore import QMargins, QModelIndex, QPersistentModelIndex, QRect, QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen

from melon.todo import Todo

from .taskwidgets import UserRole

ONE_DAY = datetime.timedelta(days=1)


class TaskItemEditorFactory(QtWidgets.QItemEditorFactory):
    """Factory for task item *editors*."""

    def __init__(self) -> None:
        """Initialise the editor factory, creating a ThreadPool"""
        super().__init__()
        self.threadPool = QThreadPool()

    def createEditor(self, userType: int, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """
        Args:
            userType (int): Argument
            parent (QWidget): Argument

        Returns:
            (QWidget):
        """
        edit = QtWidgets.QLineEdit(parent)
        edit.setAlignment(Qt.AlignmentFlag.AlignTop)
        edit.setContentsMargins(18 + 32 + 10, 2, 2, 4)
        label = QtWidgets.QLabel("Adding task...", edit)
        label.setFixedWidth(245)
        label.move(parent.width() - 250, 22)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        # edit.textChanged.connect(self.textChangeHandler(edit, label))
        return edit

    def textChangeHandler(self, edit: QtWidgets.QLineEdit, label: QtWidgets.QLabel) -> Callable:
        """Returns a handler function for keypress events on the editor.
        The handler interacts with a timer to prevent computing too frequently.

        Args:
            edit (QtWidgets.QLineEdit): the line edit widget whose events we are catching
            label (QtWidgets.QLabel): the label to display information in

        Returns:
            Callable: the event handler
        """

        def actualHandler():
            """I am called to perform the actual parsing."""
            text = edit.text()
            results = dateparser.search.search_dates(text, languages=("en", "de"))
            print(results)
            if results:
                token, stamp = results[0]
                label.setText(stamp.strftime("%d.%m.%Y"))
            else:
                label.clear()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(100)
        timer.timeout.connect(lambda: self.threadPool.start(actualHandler))

        def handler():
            """I am called on each keystroke of the QLineEdit."""
            timer.start()

        return handler


class TaskItemDelegate(QtWidgets.QStyledItemDelegate):
    """The task item delegate responsible for rendering todos (= tasks)."""

    editorDestroyed = Signal(QModelIndex)

    def __init__(self, parent):
        """
        Args:
            parent (QObject | None, optional): Argument
                (default is None)
        """
        super().__init__(parent)
        self.setItemEditorFactory(TaskItemEditorFactory())

    def destroyEditor(self, editor: QtWidgets.QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        """
        Args:
            editor (QWidget): Argument
            index (Union[QModelIndex, QPersistentModelIndex]): Argument
        """
        super().destroyEditor(editor, index)
        self.editorDestroyed.emit(index)

    def paint(
        self,
        painter: QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ):
        """
        Args:
            painter (QPainter): Argument
            option (QStyleOptionViewItem): Argument
            index (Union[QModelIndex, QPersistentModelIndex]): Argument
        """
        todo: Todo = index.data(UserRole)
        if todo is None:
            return

        rect: QRect = option.rect  # type: ignore
        painter.save()
        if todo.priority < 3:
            painter.setPen(QColor(255, 100, 100))
        elif todo.priority < 7:
            painter.setPen(QColor(33, 150, 243))
        painter.drawText(rect.translated(18 + 32 + 14, 3), todo.summary)

        dueDate = todo.dueDate
        if dueDate:
            dueTime = todo.dueTime
            text = dueDate.strftime("%d.%m.%Y")
            today = datetime.date.today()
            if dueDate == today:
                text = "today"
            elif dueDate == today - ONE_DAY:
                text = "yesterday"
            elif dueDate == today + ONE_DAY:
                text = "tomorrow"
            painter.setPen(QPen(QColor(255, 100, 100) if dueDate < today else QColor(150, 150, 150)))
            if dueTime is not None:
                text += ", " + dueTime.strftime("%H:%M")
            painter.drawText(rect.translated(-10, 3), text, Qt.AlignmentFlag.AlignRight)

        path = QPainterPath()
        path.addRoundedRect(rect.marginsRemoved(QMargins(2, 2, 2, 4)), 6, 6)
        painter.setPen(QPen(QColor(0, 255, 0, 150)))
        painter.fillPath(path, QColor(200, 200, 200, 30))
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:  # type: ignore
            path = QPainterPath()
            path.addRoundedRect(QRect(rect.x() + 2, rect.y() + 2, 8, 44), 6, 6)
            painter.fillPath(path, QColor(33, 150, 243, 200))

        if todo.calendarName is not None:
            path = QPainterPath()
            path.addRoundedRect(QRect(rect.x() + 60, rect.y() + 25, len(todo.calendarName) * 8 + 12, 16), 10, 10)
            painter.drawPath(path)
            painter.setFont(QFont("Monospace", 9))
            painter.drawText(rect.translated(32 + 14 + 22, 26), todo.calendarName)

        painter.restore()

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Args:
            option (QStyleOptionViewItem): Argument
            index (QModelIndex): Argument

        Returns:
            (QSize):
        """
        return QSize(100, 50)
