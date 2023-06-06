import logging
import pathlib

import caldav
import icalendar
import vobject

from .config import CONFIG, CONFIG_FOLDER


class TodoList:
    def __init__(self) -> None:
        self.client = caldav.DAVClient(
            CONFIG["client"]["url"],
            username=CONFIG["client"]["username"],
            password=CONFIG["client"]["password"],
        )
        self.calendars = []
        self.tasks = []

    def connect(self):
        self.principal = self.client.principal()
        logging.info("Obtained principal")

        self.calendars = self.principal.calendars()
        logging.info(f"Obtained {len(self.calendars)} calendars")

    def fetch(self):
        self.tasks = []
        for calendar in self.calendars[:2]:
            self.tasks.extend(calendar.todos())
        logging.info(f"Fetched {len(self.tasks)} tasks")

    def store(self):
        for calendar in self.calendars:
            cal = vobject.iCalendar()
            for task in calendar.todos():
                cal.add(task.vobject_instance.contents["vtodo"][0])
            with open(CONFIG_FOLDER / f"{calendar.name}.dav", "w") as f:
                cal.serialize(f)

    def load(self):
        for filename in CONFIG_FOLDER.glob("*.dav"):
            path = pathlib.Path(filename)
            with open(filename) as f:
                cal = icalendar.Calendar.from_ical(f.read())
                for task in cal.subcomponents:
                    todo = caldav.Todo(self.client)
                    todo.icalendar_instance = task
                    todo.vobject_instance.contents["calendar"] = path.stem
                    if "summary" not in todo.vobject_instance.contents:
                        # print("Skipped", filename, todo.vobject_instance)
                        continue
                    self.tasks.append(todo)
                self.calendars.append(caldav.Calendar(self.client, name=path.stem))
