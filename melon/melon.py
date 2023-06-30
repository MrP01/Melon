"""This file is the main entry point of the melon package, containing the Melon class,
the main point of contact for users of this package. It can be initialised like this:

melon = Melon()
melon.autoInit()
"""
import datetime
import json
import logging
import uuid
from typing import Iterable, Mapping

import caldav
import caldav.lib.url
import icalendar

from .calendar import Calendar, Syncable
from .config import CONFIG, CONFIG_FOLDER
from .scheduler import MCMCScheduler, TimeSlot
from .todo import Todo


class Melon:
    """The Melon class, wrapping a caldav client and principal, loading specifics from the config.
    Through me, users have access to calendars and todos.
    I also handle load, sync and store functionality.
    """

    HIDDEN_CALENDARS = ("calendar", None)

    def __init__(
        self,
        url=CONFIG["client"]["url"],
        username=CONFIG["client"]["username"],
        password=CONFIG["client"]["password"],
    ) -> None:
        """Initialises the Melon client

        Args:
            url (str, optional): URL to the CalDAV server. Defaults to CONFIG["client"]["url"].
            username (str, optional): Username. Defaults to CONFIG["client"]["username"].
            password (str, optional): Password. Defaults to CONFIG["client"]["password"].
        """
        self.client = caldav.DAVClient(url=url, username=username, password=password)
        self.calendars: dict[str, Calendar] = {}
        self.principal = None

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
                assert isinstance(object, Todo)
                self.addOrUpdateTask(object)

    def fetch(self):
        """
        Args:
        """
        if not self.calendars:
            self.connect()
        for calendar in self.calendars.values():
            assert calendar.name is not None
            calendar.syncable = Syncable.upgrade(calendar.objects_by_sync_token(load_objects=True), calendar.name)
            self._load_syncable_tasks(calendar)
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")

    def store(self):
        """
        Args:
        """
        for calendar in self.calendars.values():
            calendar.storeToFile()
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
            self.calendars[name] = Calendar.loadFromFile(
                self.client, self.principal, name, data[name]["token"], data[name]["url"]
            )
        logging.info(f"Loaded {len(self.calendars)} calendars from disk.")
        for calendar in self.calendars.values():
            self._load_syncable_tasks(calendar)

    def autoInit(self):
        """
        Args:
        """
        tokensfile = CONFIG_FOLDER / "synctokens.json"
        if not tokensfile.exists():
            self.fetch()
        else:
            self.load()

    def syncCalendar(self, calendar: Calendar):
        """
        Args:
            calendar: Argument
        """
        calendar.sync()
        self._load_syncable_tasks(calendar)

    def syncAll(self):
        """
        Args:
        """
        for calendar in self.calendars.values():
            self.syncCalendar(calendar)

    def allTasks(self) -> Iterable[Todo]:
        """Returns an iterable of all tasks in all calendars as a single list

        Yields:
            Iterator[Iterable[Todo]]: iterator of all tasks
        """
        for calendar in self.calendars.values():
            if calendar.syncable is None:
                continue
            for object in calendar.syncable.objects:
                if object.uid is None or not object.isTodo():
                    continue
                yield object

    def allIncompleteTasks(self) -> Iterable[Todo]:
        """Returns all incomplete todos

        Yields:
            Iterator[Iterable[Todo]]: incomplete todos
        """
        for todo in self.allTasks():
            if todo.isIncomplete():
                yield todo

    def getTask(self, uid: str) -> Todo:
        """Returns task with given UID

        Args:
            uid (str): the Unique Identifier

        Raises:
            ValueError: when the task could not be found

        Returns:
            Todo: the Todo with given uid
        """
        for object in self.allTasks():
            if object.uid == uid:
                return object
        raise ValueError(f"Task with UID {uid} not found.")

    def findTask(self, string: str) -> Iterable[Todo]:
        """Finds a task given a search query

        Args:
            string (str): the search query.

        Yields:
            Iterator[Iterable[Todo]]: the generated search results.
        """
        for object in self.allTasks():
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
        schedule.add("prodid", "-//Melon//example.org//")
        schedule.add("version", "2.0")
        todos = {t.uid: t for t in self.allTasks()}
        for uid, slot in scheduling.items():
            print("Adding", uid)
            event = icalendar.Event(summary=todos[uid].summary)
            event.add("dtstart", slot.timestamp)
            event.add("dtend", slot.end)
            event.add("dtstamp", datetime.datetime.now())
            event.add("uid", uuid.uuid4())
            schedule.add_component(event)
        return schedule

    def scheduleAllAndExport(self, file: str):
        """Runs the scheduler on all tasks and exports as an ICS file.

        Args:
            file (str): filesystem path that the ics file should be exported to
        """
        logging.info("Initialising scheduler.")
        scheduler = MCMCScheduler(list(map(Todo.toTask, self.allIncompleteTasks())))
        logging.info(f"Scheduling {len(scheduler.tasks)} now.")
        schedule = scheduler.schedule()
        logging.info("Exporting.")
        export = self.exportScheduleAsCalendar(schedule)
        logging.info("Export calendar created.")
        # print(export.to_ical().decode().replace("\r\n", "\n"))
        with open(file, "wb") as f:
            f.write(export.to_ical())
        logging.info("Finished export.")
