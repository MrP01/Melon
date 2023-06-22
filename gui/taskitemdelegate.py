"""This module defines how tasks should be rendered in the GUI."""
import datetime

from PySide6.QtCore import QMargins, QModelIndex, QObject, QPersistentModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QItemEditorFactory, QLineEdit, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from melon.todo import Todo

from .taskwidgets import UserRole

ONE_DAY = datetime.timedelta(days=1)


class TaskItemEditorFactory(QItemEditorFactory):
    """Factory for task item *editors*."""

    def createEditor(self, userType: int, parent: QWidget) -> QWidget:
        """
        Args:
                userType (int) : Argument
                parent (QWidget) : Argument

        Returns:
            (QWidget):
        """
        edit = QLineEdit(parent)
        edit.setAlignment(Qt.AlignmentFlag.AlignTop)
        edit.setContentsMargins(18 + 32 + 10, 2, 2, 4)
        return edit


class TaskItemDelegate(QStyledItemDelegate):
    """The task item delegate responsible for rendering todos (= tasks)."""

    editorDestroyed = Signal(QModelIndex | QPersistentModelIndex)

    def __init__(self, parent: QObject | None = None):
        """
        Args:
            parent (Union[QObject, None], optional) : Argument
                (default is None)
        """
        super().__init__(parent)
        self.setItemEditorFactory(TaskItemEditorFactory())

    def destroyEditor(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        """
        Args:
            editor (QWidget) : Argument
            index (Union[QModelIndex, QPersistentModelIndex]) : Argument

        """
        super().destroyEditor(editor, index)
        self.editorDestroyed.emit(index)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        """
        Args:
            painter (QPainter) : Argument
            option (QStyleOptionViewItem) : Argument
            index (Union[QModelIndex, QPersistentModelIndex]) : Argument
        """
        todo: Todo = index.data(UserRole)
        if todo is None:
            return

        rect: QRect = option.rect  # type: ignore
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
            print(dueDate.time())
            if dueDate.time() != datetime.time():
                text += ", " + dueDate.strftime("%H:%M")
            painter.drawText(rect.translated(-10, 3), text, Qt.AlignmentFlag.AlignRight)

        path = QPainterPath()
        path.addRoundedRect(rect.marginsRemoved(QMargins(2, 2, 2, 4)), 6, 6)
        painter.setPen(QPen(QColor(0, 255, 0, 150)))
        painter.fillPath(path, QColor(200, 200, 200, 30))
        if option.state & QStyle.StateFlag.State_Selected:  # type: ignore
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
        """
        Args:
                option (QStyleOptionViewItem) : Argument
                index (QModelIndex) : Argument

        Returns:
            (QSize):
        """
        return QSize(100, 50)
