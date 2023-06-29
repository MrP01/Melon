"""This file is the main entry point of the melon package, containing the Melon class,
the main point of contact for users of this package. It can be initialised like this:

melon = Melon()
melon.startup()
"""
import json
import logging
from typing import Iterable, Mapping

import caldav
import caldav.lib.url
import icalendar

from melon.scheduler import TimeSlot

from .calendar import Calendar, Syncable
from .config import CONFIG, CONFIG_FOLDER
from .todo import Todo


class Melon:
    """The Melon class, wrapping a caldav client and principal, loading specifics from the config.
    Through me, users have access to calendars and todos.
    I also handle load, sync and store functionality.
    """

    HIDDEN_CALENDARS = ("calendar", None)

    def __init__(self) -> None:
        """
        Args:
        """
        self.client = caldav.DAVClient(
            CONFIG["client"]["url"],
            username=CONFIG["client"]["username"],
            password=CONFIG["client"]["password"],
        )
        self.principal = None
        self.calendars: dict[str, Calendar] = {}

    def connect(self):
        """
        Args:
        """
        self.principal = self.client.principal()
        logging.info("Obtained principal")

        all_calendars = self.principal.calendars()
        self.calendars = {cal.name: Calendar(cal) for cal in all_calendars if cal.name not in self.HIDDEN_CALENDARS}
        logging.info(f"Obtained {len(self.calendars)} calendars")

    def _load_syncable_tasks(self, calendar):
        """
        Args:
            calendar: Argument
        """
        for object in calendar.syncable:
            if "vtodo" in object.vobject_instance.contents:
                todo = Todo.upgrade(object, calendar.name)
                self.addOrUpdateTask(todo)

    def initialFetch(self):
        """
        Args:
        """
        if not self.calendars:
            self.connect()
        for calendar in self.calendars.values():
            calendar.syncable = Syncable.upgrade(calendar.objects_by_sync_token(load_objects=True))
            self._load_syncable_tasks(calendar)
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")

    def store(self):
        """
        Args:
        """
        for calendar in self.calendars.values():
            calendar.store_to_file()
        with open(CONFIG_FOLDER / "synctokens.json", "w") as f:
            json.dump({cal.name: cal.storageObject() for cal in self.calendars.values()}, f)
        logging.info(f"Stored {len(self.calendars)} calendars to disk.")

    def load(self):
        """
        Args:
        """
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

    def init(self):
        """
        Args:
        """
        tokensfile = CONFIG_FOLDER / "synctokens.json"
        if not tokensfile.exists():
            self.initialFetch()
        else:
            self.load()

    def syncCalendar(self, calendar):
        """
        Args:
            calendar: Argument
        """
        updated, deleted = calendar.syncable.sync()
        calendar.syncable.objects = list(calendar.syncable.objects)
        self._load_syncable_tasks(calendar)
        logging.info(
            f"Synced {calendar.name:48} ({len(updated)} updated and {len(deleted)} deleted entries.) "
            f"In total, we have {len(calendar.syncable)} objects."
        )

    def syncAll(self):
        """
        Args:
        """
        for calendar in self.calendars.values():
            self.syncCalendar(calendar)

    def getTask(self, uid: str) -> Todo:
        """Returns task with given UID

        Args:
            uid (str): the Unique Identifier

        Raises:
            ValueError: when the task could not be found

        Returns:
            Todo: the Todo with given uid
        """
        for calendar in self.calendars.values():
            if calendar.syncable is None:
                continue
            for object in calendar.syncable.objects:
                if object.uid == uid:
                    return object
        raise ValueError(f"Task with UID {uid} not found.")

    def findTask(self, string: str) -> Iterable[Todo]:
        """Finds a task given a search query

        Args:
            string (str): the search query.

        Returns:
            Iterable[Todo]: the generated search results.
        """
        for calendar in self.calendars.values():
            if calendar.syncable is None:
                continue
            for object in calendar.syncable.objects:
                if string in object.data and object.isTodo():
                    yield object

    def addOrUpdateTask(self, todo: Todo):
        """
        Args:
            todo (Todo): Argument
        """

    def exportScheduleAsCalendar(self, scheduling: Mapping[str, TimeSlot]) -> icalendar.Calendar:
        """A read-only ICS calendar containing scheduled tasks. Can be stored to disk using schedule.to_ical().

        Args:
            scheduling (Mapping[str, TimeSlot]): Mapping of task UID to TimeSlot

        Returns:
            icalendar.Calendar: the calendar containing events (time slots) proposed for the completion of tasks
        """
        schedule = icalendar.Calendar()
        for uid, slot in scheduling.items():
            todo = self.getTask(uid)
            schedule.add_component(icalendar.Event(summary=todo.summary, start=slot.timestamp, end=slot.end))
        return schedule
