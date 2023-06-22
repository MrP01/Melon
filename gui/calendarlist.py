"""In this submodule, we define the calendar list widget (on the left)."""
from typing import Iterable

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QItemDelegate, QListWidget, QListWidgetItem, QSizePolicy, QStyleOptionViewItem, QWidget

from melon.calendar import Calendar


class LargerListViewDelegate(QItemDelegate):
    """An item delegate that slightly increases the display size of each item."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        """Returns a size hint for each list widget item, constant in this case.

        Args:
                option (QStyleOptionViewItem) : Argument
                index (Union[QModelIndex, QPersistentModelIndex]) : Argument

        Returns:
            (QSize):
        """
        return QSize(100, 27)


class CalendarListView(QListWidget):
    """QListWidget subclass that shows the list of calendars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Args:
            parent (Union[QWidget, None], optional) : Argument
                (default is None)

        """
        super().__init__(parent)
        self.setItemDelegate(LargerListViewDelegate())
        policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        policy.setHorizontalStretch(2)
        self.setSizePolicy(policy)

        homeItem = QListWidgetItem(QIcon.fromTheme("go-home"), "All Tasks")
        homeItem.setData(Qt.ItemDataRole.UserRole, {"is-special": True, "specialty": "all"})
        self.addItem(homeItem)

    def populate(self, calendars: Iterable[Calendar]):
        """
        Args:
            calendars (Iterable[Calendar]) : Argument
        """
        icon = QIcon.fromTheme("view-list-symbolic")
        for calendar in calendars:
            assert calendar.name is not None
            item = QListWidgetItem(icon, calendar.name)
            self.addItem(item)
        self.sortItems()
