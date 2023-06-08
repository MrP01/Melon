import logging
import pathlib

import caldav
import icalendar
import vobject

from .config import CONFIG, CONFIG_FOLDER


class Calendar(caldav.Calendar):
    def __init__(self, calendar: caldav.Calendar) -> None:
        """A copy constructor"""
        super().__init__(
            calendar.client,
            calendar.url,
            calendar.parent,
            calendar.name,
            calendar.id,
            calendar.props,
            calendar.extra_init_options,
        )


class Todo(caldav.Todo):
    def __init__(self, todo: caldav.Todo):
        """A copy constructor"""
        super().__init__(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props)
        # if "summary" not in self.vobject_instance.contents:
        #     self.vobject_instance = self.vobject_instance.contents["vtodo"][0]
        self.calendarName = None

    def save(
        self,
        no_overwrite: bool = False,
        no_create: bool = False,
        obj_type: str | None = None,
        increase_seqno: bool = True,
        if_schedule_tag_match: bool = False,
    ):
        print("Saving! :)")
        return super().save(no_overwrite, no_create, obj_type, increase_seqno, if_schedule_tag_match)

    def __str__(self) -> str:
        return "I am a TODO!"

    def __repr__(self) -> str:
        return "TODO"

    @property
    def summary(self):
        return self.vobject_instance.contents["summary"][0].value


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

        self.calendars = [Calendar(cal) for cal in self.principal.calendars()]
        logging.info(f"Obtained {len(self.calendars)} calendars")

    def fetch(self):
        self.tasks = []
        for calendar in self.calendars[:2]:
            self.tasks.extend([Todo(todo) for todo in calendar.todos()])
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
                    todo = Todo(caldav.Todo(self.client))
                    todo.icalendar_instance = task
                    todo.calendarName = path.stem
                    if "summary" not in todo.vobject_instance.contents:
                        # print("Skipped", filename, todo.vobject_instance)
                        continue
                    self.tasks.append(todo)
                self.calendars.append(caldav.Calendar(self.client, name=path.stem))
