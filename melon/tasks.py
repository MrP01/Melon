import datetime
import json
import logging
import pickle

import caldav
import vobject

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
        self.syncable = None


class Todo(caldav.Todo):
    def __init__(self, todo: caldav.Todo, calendarName: str):
        """A copy constructor"""
        super().__init__(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props)
        self.calendarName = calendarName

    def save(
        self,
        no_overwrite: bool = False,
        no_create: bool = False,
        obj_type: str | None = None,
        increase_seqno: bool = True,
        if_schedule_tag_match: bool = False,
    ):
        # print("Saving! :)")
        return super().save(no_overwrite, no_create, obj_type, increase_seqno, if_schedule_tag_match)

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

        all_calendars = self.principal.calendars()
        self.calendars = {cal.name: Calendar(cal) for cal in all_calendars if cal.name not in self.HIDDEN_CALENDARS}
        logging.info(f"Obtained {len(self.calendars)} calendars")

    # def fetch(self):
    #     self.tasks = []
    #     for name, calendar in self.calendars.items():
    #         self.tasks.extend([Todo(todo, name) for todo in calendar.todos()])
    #         break
    #     logging.info(f"Fetched {len(self.tasks)} tasks")

    def initial_fetch(self):
        if not self.calendars:
            self.connect()
        for name, calendar in self.calendars.items():
            cal = vobject.iCalendar()
            calendar.syncable = calendar.objects(load_objects=True)
            for task in calendar.syncable:
                cal.add(task.vobject_instance)
                self.tasks.append(Todo(task, calendar.name))
            with open(CONFIG_FOLDER / f"{calendar.name}.dav", "w") as f:
                cal.serialize(f)
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")
            break

    def store(self):
        syncTokenStorage = {}
        for name, calendar in self.calendars.items():
            if calendar.syncable is not None:
                syncTokenStorage[name] = calendar.syncable.sync_token
            cal = vobject.iCalendar()
            for task in calendar.syncable:
                cal.add(task.vobject_instance)
            with open(CONFIG_FOLDER / f"{calendar.name}.dav", "w") as f:
                cal.serialize(f)
            logging.info(f"Stored {len(calendar.syncable)} objects.")
            break
        with open(CONFIG_FOLDER / "synctokens.json", "w") as f:
            json.dump(syncTokenStorage, f)

    def load_and_sync(self):
        if self.principal is None:
            self.principal = self.client.principal()
        with open(CONFIG_FOLDER / "calendars.pickle") as f:
            self.calendars: dict[str, Calendar] = pickle.load(f)
        logging.info(f"Loaded {len(self.calendars)} calendars from disk.")
        # for filename in CONFIG_FOLDER.glob("*.dav"):
        #     path = pathlib.Path(filename)
        #     calendarName = path.stem
        #     if calendarName in self.HIDDEN_CALENDARS:
        #         continue
        #     with open(filename) as f:
        #         cal = icalendar.Calendar.from_ical(f.read())
        #         objects = []
        #         for task in cal.subcomponents:
        #             todo = Todo(caldav.Todo(self.client), calendarName)
        #             todo.icalendar_instance = task
        #             if "vtodo" not in todo.vobject_instance.contents:
        #                 # print("Skipped", filename, todo.vobject_instance)
        #                 continue
        #             objects.append(todo)
        #             self.tasks.append(todo)

        for name, calendar in self.calendars.items():
            # calendar = Calendar(self.principal.calendar(name=calendarName))
            # calendar.syncable = calendar.objects_by_sync_token(sync_token=syncTokenStorage[calendarName])
            updated, deleted = calendar.syncable.sync()
            logging.info(
                f"Synced, resulting in {len(updated)} updated and {len(deleted)} deleted entries. "
                f"In total, we have {len(calendar.syncable)} objects."
            )
            break

    def startup(self):
        # self.connect()
        tokensfile = CONFIG_FOLDER / "synctokens.json"
        if not tokensfile.exists():
            self.initial_fetch()
        else:
            self.load_and_sync()
