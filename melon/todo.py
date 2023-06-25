"""This module contains the Todo class."""
import datetime
from typing import Literal

import caldav
import caldav.lib.url
import icalendar.cal
import icalendar.prop
import vobject


class Todo(caldav.Todo):
    """A class representing todos (= tasks), subclassing the caldav.Todo object which in turn stores VTODO data."""

    vobject_instance: vobject.base.Component
    icalendar_component: icalendar.cal.Todo

    def __init__(self, *args, calendarName: str | None = None, **kwargs):
        """Initialises the base class"""
        super().__init__(*args, **kwargs)
        self.calendarName = calendarName

    @staticmethod
    def upgrade(todo: caldav.Todo, calendarName: str) -> "Todo":
        """A copy constructor

        Args:
            todo (caldav.Todo): Argument
            calendarName (str): Argument
        """
        return Todo(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props, calendarName=calendarName)

    @property
    def vtodo(self) -> vobject.base.Component:
        """
        Returns:
            (vobject.base.Component):
        """
        return self.vobject_instance.contents["vtodo"][0]  # type: ignore

    @property
    def summary(self) -> str:
        """
        Returns:
            (str):
        """
        return self.vtodo.contents["summary"][0].value  # type: ignore

    @summary.setter
    def summary(self, value: str):
        """
        Args:
            value (str): Argument
        """
        self.vtodo.contents["summary"][0].value = value  # type: ignore

    @property
    def dueDate(self) -> datetime.date | None:
        """
        Returns:
            (datetime.datetime | datetime.date | None):
        """
        if "due" in self.vtodo.contents:
            due = self.vtodo.contents["due"][0].value  # type: ignore
            if isinstance(due, datetime.datetime):
                return due.date()
            return due  # otherwise, this value is already a datetime.date

    @dueDate.setter
    def dueDate(self, value: datetime.date | None) -> None:
        """Sets my due date.

        Args:
            value (datetime.date): Date to set.
        """
        if value is None:
            del self.icalendar_component["due"]
        else:
            self.icalendar_component["due"] = icalendar.prop.vDDDTypes(value)

    @property
    def dueTime(self) -> datetime.time | None:
        """
        Returns:
            (datetime.datetime | datetime.date | None):
        """
        if "due" in self.vtodo.contents:
            due = self.vtodo.contents["due"][0].value  # type: ignore
            if isinstance(due, datetime.datetime):
                return due.time()

    @property
    def uid(self) -> str | None:
        """
        Returns:
            (Union[str, None]):
        """
        try:
            return self.vtodo.contents["uid"][0].value  # type: ignore
        except KeyError:
            return

    @property
    def priority(self) -> int:
        """
        Returns:
            int: the priority of the task, an integer between 1 and 9,
                 where 1 corresponds to the highest and 9 to the lowest priority
        """
        value = self.icalendar_component.get("priority")
        return int(value) if value is not None else 9

    def isIncomplete(self) -> bool:
        """
        Returns:
            (bool):
        """
        return "STATUS:NEEDS-ACTION" in self.data or (
            not "\nCOMPLETED:" in self.data
            and not "\nSTATUS:COMPLETED" in self.data
            and not "\nSTATUS:CANCELLED" in self.data
        )

    def isComplete(self) -> bool:
        """
        Returns:
            (bool):
        """
        return not self.isIncomplete()

    def complete(
        self,
        completion_timestamp: datetime.datetime | None = None,
        handle_rrule: bool = True,
        rrule_mode: Literal["safe", "this_and_future"] = "safe",
    ) -> None:
        """
        Args:
            completion_timestamp (Union[datetime.datetime, None], optional): Argument
                (default is None)
            handle_rrule (bool, optional): Argument
                (default is True)
            rrule_mode (Literal['safe', 'this_and_future'], optional): Argument
                (default is 'safe')

        """
        super().complete(completion_timestamp, handle_rrule, rrule_mode)
        print("Task completed.")

    def isTodo(self) -> bool:
        """
        Returns:
            bool: whether this object is a VTODO or not (i.e. an event or journal).
        """
        return isinstance(self.icalendar_component, icalendar.cal.Todo)

    def __str__(self) -> str:
        """
        Returns:
            (str):
        """
        return self.summary

    def __repr__(self) -> str:
        """
        Returns:
            (str):
        """
        return f"<Melon.Todo: {self.summary}>"
