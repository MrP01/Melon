import logging

from PySide6 import QtCore, QtWidgets

from melon.todo import Todo


class TaskContextMenu(QtWidgets.QMenu):
    dueDateChanged = QtCore.Signal()

    def __init__(self, todo: Todo):
        super().__init__()
        self.todo = todo

    def buildUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.calendarWidget = QtWidgets.QCalendarWidget()
        self.calendarWidget.setSelectedDate(self.todo.dueDate)
        self.calendarWidget.selectionChanged.connect(self.handleDateChange)
        layout.addWidget(self.calendarWidget)
        self.setLayout(layout)

    def handleDateChange(self):
        date = self.calendarWidget.selectedDate()
        self.todo.dueDate = date.toPython()
        self.todo.save()
        logging.info(f"Changed due date: {self.todo.dueDate}")
        self.dueDateChanged.emit()
