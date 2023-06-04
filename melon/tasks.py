import logging

import caldav
import vobject

from .config import CONFIG, CONFIG_FOLDER


class TodoList:
    def __init__(self) -> None:
        self.client = caldav.DAVClient(
            CONFIG["client"]["url"],
            username=CONFIG["client"]["username"],
            password=CONFIG["client"]["password"],
        )
        self.principal = self.client.principal()
        logging.info("Obtained principal")

        self.calendars = self.principal.calendars()
        logging.info(f"Obtained {len(self.calendars)} calendars")

        self.tasks = []

    def fetch(self):
        self.tasks = []
        for calendar in self.calendars[:2]:
            self.tasks.extend(calendar.todos())
        logging.info(f"Fetched {len(self.tasks)} tasks")

    def store(self):
        for calendar in self.calendars:
            cal = vobject.iCalendar()
            for task in self.tasks:
                cal.add(task.vobject_instance.contents["vtodo"][0])
            with open(CONFIG_FOLDER / f"{calendar.name}.dav") as f:
                cal.serialize(f)
