import json
import logging

import caldav
import caldav.lib.url

from .calendar import Calendar
from .config import CONFIG, CONFIG_FOLDER
from .todo import Todo


class TodoList:
    HIDDEN_CALENDARS = ("calendar", None)

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
            calendar.syncable = calendar.objects_by_sync_token(load_objects=True)
            self._load_syncable_tasks(calendar)
            logging.info(f"Fetched {len(calendar.syncable)} full objects!")

    def store(self):
        for calendar in self.calendars.values():
            calendar.store_to_file()
        with open(CONFIG_FOLDER / "synctokens.json", "w") as f:
            json.dump({cal.name: cal.storageObject() for cal in self.calendars.values()}, f)
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
            f"Synced {calendar.name:48} ({len(updated)} updated and {len(deleted)} deleted entries.) "
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
