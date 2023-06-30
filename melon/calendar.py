"""This module contains the Calendar class."""
import logging
from typing import Iterable

import caldav
import caldav.lib.url
import icalendar
import vobject

from .config import CONFIG_FOLDER
from .todo import NEW_TASK_TEXT, Todo


class Calendar(caldav.Calendar):
    """Class representing a calendar (or todo list, if you want to call it that, this name is given by CalDAV).
    A calendar is a collection of objects that can be synced to a CalDAV server.
    In this implementation, the objects are stored within the `syncable` subclass.
    """

    def __init__(self, calendar: caldav.Calendar) -> None:
        """A copy constructor

        Args:
            calendar (caldav.Calendar): Argument
        """
        super().__init__(
            calendar.client,
            calendar.url,
            calendar.parent,
            calendar.name,
            calendar.id,
            calendar.props,
            **calendar.extra_init_options,
        )
        self.syncable: Syncable | None = None

    def storeToFile(self):
        """Save the calendar objects to a local file on disk, in iCal format."""
        ical = vobject.iCalendar()
        assert self.syncable is not None
        for task in self.syncable:
            ical.add(task.vobject_instance)
        with open(CONFIG_FOLDER / f"{self.name}.dav", "w") as f:
            ical.serialize(f)  # type: ignore

    @staticmethod
    def loadFromFile(client: caldav.DAVClient, principal: caldav.Principal, name: str, sync_token: str, url: str):
        """
        Args:
            client (caldav.DAVClient): Argument
            principal (caldav.Principal): Argument
            name (str): Argument
            sync_token (str): Argument
            url (str): Argument
        """
        cal_url = caldav.lib.url.URL(url)
        with open(CONFIG_FOLDER / f"{name}.dav") as f:
            ical = icalendar.Calendar.from_ical(f.read())
        objects = []
        cal = Calendar(caldav.Calendar(client, parent=principal.calendar_home_set, name=name, url=url))
        for task in ical.subcomponents:
            todo = Todo.upgrade(caldav.Todo(client, parent=cal), name)
            todo.icalendar_instance = task
            todo.url = cal_url.join(str(task.subcomponents[0].get("uid")) + ".ics")
            objects.append(todo)
        cal.syncable = Syncable(cal, objects, sync_token)
        logging.info(f"Calendar {name}: loaded {len(objects)} objects.")
        return cal

    def createTodo(self, summary: str = NEW_TASK_TEXT):
        """
        Args:
            summary (str): Argument
        """
        assert self.name is not None
        return Todo(
            self.client,
            data=self._use_or_create_ics(f"SUMMARY:{summary}", objtype="VTODO"),  # type: ignore
            parent=self,
            calendarName=self.name,
        )

    def storageObject(self) -> dict:
        """
        Returns:
            (dict):
        """
        assert self.syncable is not None
        return {
            "url": str(self.url),
            "token": self.syncable.sync_token,
        }

    def sync(self):
        """Synchronise me"""
        assert self.name is not None
        assert self.syncable is not None
        updated, deleted = self.syncable.sync()
        self.syncable.objects = [
            todo if isinstance(todo, Todo) else Todo.upgrade(todo, self.name) for todo in self.syncable.objects
        ]
        logging.info(
            f"Synced {self.name:48} ({len(updated)} updated and {len(deleted)} deleted entries.) "
            f"In total, we have {len(self.syncable)} objects."
        )


class Syncable(caldav.SynchronizableCalendarObjectCollection):
    """The synchronisable collection of CalDAV objects, handling efficient syncs between server and client."""

    calendar: Calendar
    objects: Iterable[Todo]
    sync_token: str

    @staticmethod
    def upgrade(synchronisable: caldav.SynchronizableCalendarObjectCollection) -> "Syncable":
        """Upgrades the third-party caldav.SynchronizableCalendarObjectCollection to a Syncable

        Args:
            synchronisable (caldav.SynchronizableCalendarObjectCollection): the original instance

        Returns:
            (Syncable): the syncable
        """
        return Syncable(synchronisable.calendar, synchronisable.objects, synchronisable.sync_token)  # type: ignore
