from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from melon.tasks import Calendar


class LargerListViewDelegate(QItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        return QSize(100, 27)


class CalendarList(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setItemDelegate(LargerListViewDelegate())
        policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        policy.setHorizontalStretch(2)
        self.setSizePolicy(policy)

        homeItem = QListWidgetItem(QIcon.fromTheme("go-home"), "All Tasks")
        homeItem.setData(Qt.ItemDataRole.UserRole, {"is-special": True, "specialty": "all"})
        self.addItem(homeItem)

    def populate(self, calendars: list[Calendar]):
        icon = QIcon.fromTheme("view-list-symbolic")
        for calendar in calendars:
            item = QListWidgetItem(icon, calendar.name)
            self.addItem(item)
        self.sortItems()
