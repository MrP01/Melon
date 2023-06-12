import datetime
import logging
import pickle

import caldav

from .config import CONFIG, CONFIG_FOLDER

EMPTY_TODO_DATA = """
BEGIN:VCALENDAR
BEGIN:VTODO
SUMMARY: {summary}
END:VTODO
END:VCALENDAR
"""


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
            **calendar.extra_init_options,
        )
        self.syncable: caldav.SynchronizableCalendarObjectCollection | None = None


class Todo(caldav.Todo):
    def __init__(self, todo: caldav.Todo, calendarName: str):
        """A copy constructor"""
        super().__init__(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props)
        self.calendarName = calendarName

    @property
    def vtodo(self):
        return self.vobject_instance.contents["vtodo"][0]

    @property
    def summary(self) -> str:
        return self.vtodo.contents["summary"][0].value

    @summary.setter
    def summary(self, value: str):
        self.vtodo.contents["summary"][0].value = value

    @property
    def dueDate(self) -> datetime.datetime:
        if "due" in self.vtodo.contents:
            due = self.vtodo.contents["due"][0].value
            if isinstance(due, datetime.date):
                return datetime.datetime.combine(due, datetime.time())
            return due

    def isComplete(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.summary

    def __repr__(self) -> str:
        return f"<Melon.Todo: {self.summary}>"


class TodoList:
    HIDDEN_CALENDARS = ("calendar",)

    def __init__(self) -> None:
        self.client = caldav.DAVClient(
            CONFIG["client"]["url"],
            username=CONFIG["client"]["username"],
            password=CONFIG["client"]["password"],
        )
        self.principal = None
        self.calendars: dict[str, Calendar] = {}
        self.tasks = []

    def connect(self):
        self.principal = self.client.principal()
        logging.info("Obtained principal")

        all_calendars = self.principal.calendars()[:4]
        self.calendars = {cal.name: Calendar(cal) for cal in all_calendars if cal.name not in self.HIDDEN_CALENDARS}
        logging.info(f"Obtained {len(self.calendars)} calendars")

    def initial_fetch(self):
        if not self.calendars:
            self.connect()
        for calendar in self.calendars.values():
            calendar.syncable = calendar.objects(load_objects=True)
            for object in calendar.syncable:
                if "vtodo" in object.vobject_instance.contents:
                    self.tasks.append(Todo(object, calendar.name))
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")

    def store(self):
        with open(CONFIG_FOLDER / "calendars.pickle", "wb") as f:
            pickle.dump(self.calendars, f)

    def load(self):
        if self.principal is None:
            self.principal = self.client.principal()
        with open(CONFIG_FOLDER / "calendars.pickle", "rb") as f:
            self.calendars: dict[str, Calendar] = pickle.load(f)
        logging.info(f"Loaded {len(self.calendars)} calendars from disk.")
        for calendar in self.calendars.values():
            for object in calendar.syncable:
                if "vtodo" in object.vobject_instance.contents:
                    self.tasks.append(Todo(object, calendar.name))

    def sync(self):
        for calendar in self.calendars.values():
            updated, deleted = calendar.syncable.sync()
            calendar.syncable.objects = list(calendar.syncable.objects)
            logging.info(
                f"Synced {calendar.name}, resulting in {len(updated)} updated and {len(deleted)} deleted entries. "
                f"In total, we have {len(calendar.syncable)} objects."
            )

    def startup(self):
        tokensfile = CONFIG_FOLDER / "calendars.pickle"
        if not tokensfile.exists():
            self.initial_fetch()
        else:
            self.load()
