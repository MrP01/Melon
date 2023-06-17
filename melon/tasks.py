import datetime
import json
import logging
from typing import Literal

import caldav
import caldav.lib.url
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
            **calendar.extra_init_options,
        )
        self.syncable: caldav.SynchronizableCalendarObjectCollection | None = None

    def store_to_file(self):
        ical = vobject.iCalendar()
        for task in self.syncable:
            ical.add(task.vobject_instance)
        with open(CONFIG_FOLDER / f"{self.name}.dav", "w") as f:
            ical.serialize(f)

    @staticmethod
    def load_from_file(client: caldav.DAVClient, principal: caldav.Principal, name: str, sync_token: str, url: str):
        cal_url = caldav.lib.url.URL(url)
        with open(CONFIG_FOLDER / f"{name}.dav") as f:
            ical = icalendar.Calendar.from_ical(f.read())
        objects = []
        cal = Calendar(caldav.Calendar(client, parent=principal.calendar_home_set, name=name, url=url))
        for task in ical.subcomponents:
            todo = Todo(caldav.Todo(client, parent=cal), name)
            todo.icalendar_instance = task
            todo.url = cal_url.join(str(task.subcomponents[0].get("uid")) + ".ics")
            objects.append(todo)
        cal.syncable = caldav.SynchronizableCalendarObjectCollection(cal, objects, sync_token)
        logging.info(f"Calendar {name}: loaded {len(objects)} objects.")
        return cal


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

    @property
    def uid(self) -> str | None:
        try:
            return self.vtodo.contents["uid"][0].value
        except KeyError:
            return

    def isIncomplete(self) -> bool:
        return "STATUS:NEEDS-ACTION" in self.data or (
            not "\nCOMPLETED:" in self.data
            and not "\nSTATUS:COMPLETED" in self.data
            and not "\nSTATUS:CANCELLED" in self.data
        )

    def isComplete(self) -> bool:
        return not self.isIncomplete()

    def complete(
        self,
        completion_timestamp: datetime.datetime | None = None,
        handle_rrule: bool = True,
        rrule_mode: Literal["safe", "this_and_future"] = "safe",
    ) -> None:
        super().complete(completion_timestamp, handle_rrule, rrule_mode)
        print("Task completed.")

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

    def connect(self):
        self.principal = self.client.principal()
        logging.info("Obtained principal")

        all_calendars = self.principal.calendars()
        self.calendars = {cal.name: Calendar(cal) for cal in all_calendars if cal.name not in self.HIDDEN_CALENDARS}
        logging.info(f"Obtained {len(self.calendars)} calendars")

    def _load_syncable_tasks(self, calendar):
        for object in calendar.syncable:
            if "vtodo" in object.vobject_instance.contents:
                todo = Todo(object, calendar.name)
                self.addOrUpdateTask(todo)

    def initial_fetch(self):
        if not self.calendars:
            self.connect()
        for calendar in self.calendars.values():
            calendar.syncable = calendar.objects(load_objects=True)
            self._load_syncable_tasks(calendar)
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")

    def store(self):
        for calendar in self.calendars.values():
            calendar.store_to_file()
        with open(CONFIG_FOLDER / "synctokens.json", "w") as f:
            json.dump(
                {cal.name: {"url": str(cal.url), "token": cal.syncable.sync_token} for cal in self.calendars.values()},
                f,
            )
        logging.info(f"Stored {len(self.calendars)} calendars to disk.")

    def load(self):
        if self.principal is None:
            self.principal = self.client.principal()
            logging.info("Obtained principal")
        with open(CONFIG_FOLDER / "synctokens.json") as f:
            data = json.load(f)
        for file in CONFIG_FOLDER.glob("*.dav"):
            name = file.stem  # filename corresponds to the calendar name
            self.calendars[name] = Calendar.load_from_file(
                self.client, self.principal, name, data[name]["token"], data[name]["url"]
            )
        logging.info(f"Loaded {len(self.calendars)} calendars from disk.")
        for calendar in self.calendars.values():
            self._load_syncable_tasks(calendar)

    def syncAll(self):
        for calendar in self.calendars.values():
            self.syncCalendar(calendar)

    def syncCalendar(self, calendar):
        updated, deleted = calendar.syncable.sync()
        calendar.syncable.objects = list(calendar.syncable.objects)
        self._load_syncable_tasks(calendar)
        logging.info(
            f"Synced {calendar.name}, {len(updated)} updated and {len(deleted)} deleted entries. "
            f"In total, we have {len(calendar.syncable)} objects."
        )

    def startup(self):
        tokensfile = CONFIG_FOLDER / "synctokens.json"
        if not tokensfile.exists():
            self.initial_fetch()
        else:
            self.load()

    def addOrUpdateTask(self, todo: Todo):
        pass
