import caldav
from PySide6.QtWidgets import *


class TaskItem(QListWidgetItem):
    def render(self):
        pass


class TaskListView(QListWidget):
    def populate(self, tasks: list[caldav.Todo]):
        self.clear()
        for task in tasks:
            self.addItem(TaskItem(task.vobject_instance.contents["vtodo"][0].contents["summary"][0].value))
