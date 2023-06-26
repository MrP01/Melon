"""This module contains the Todo class."""
import datetime
from typing import Literal

import caldav
import caldav.lib.url
import icalendar.cal
import icalendar.prop
import vobject

NEW_TASK_TEXT = "An exciting new task!"
MIDNIGHT = datetime.time(0, 0)


class Todo(caldav.Todo):
    """A class representing todos (= tasks), subclassing the caldav.Todo object which in turn stores VTODO data."""

    vobject_instance: vobject.base.Component  # fast access
    icalendar_component: icalendar.cal.Todo  # slow access, but does more checks

    def __init__(self, *args, calendarName: str | None = None, **kwargs):
        """Initialises the base class"""
        super().__init__(*args, **kwargs)
        self.calendarName = calendarName

    @staticmethod
    def upgrade(todo: caldav.Todo, calendarName: str) -> "Todo":
        """A copy constructor constructing a melon.Todo from a caldav.Todo

        Args:
            todo (caldav.Todo): Argument
            calendarName (str): Argument
        """
        return Todo(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props, calendarName=calendarName)

    @property
    def vtodo(self) -> vobject.base.Component:
        """Returns the VTODO object stored within me. This is faster than accessing the icalendar_component.

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
        """This method has to be fast, as it is accessed very frequently according to profiler output.
        Therefore we use do not use self.vtodo.

        Returns:
            (Union[str, None]):
        """
        try:
            return self._vobject_instance.contents["vtodo"][0].contents["uid"][0].value  # type: ignore
        except AttributeError:
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
        value = self.vtodo.contents.get("priority")
        return int(value[0].value) if value is not None else 9  # type: ignore

    def isIncomplete(self) -> bool:
        """
        Returns:
            (bool):
        """
        data = self.data
        return "STATUS:NEEDS-ACTION" in data or (
            not "\nCOMPLETED:" in data and not "\nSTATUS:COMPLETED" in data and not "\nSTATUS:CANCELLED" in data
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

    def __lt__(self, other: "Todo") -> bool:
        """Compares two todos in terms of ordering

        Args:
            other (Todo): the instance to compare with

        Returns:
            bool: whether self < other
        """
        if self.summary == NEW_TASK_TEXT:
            return False
        if other.summary == NEW_TASK_TEXT:
            return True
        if self.dueDate is None and other.dueDate is not None:
            return False
        if other.dueDate is None and self.dueDate is not None:
            return True
        return (
            self.dueDate,
            self.dueTime or MIDNIGHT,
            self.summary,
        ) < (
            other.dueDate,
            other.dueTime or MIDNIGHT,
            other.summary,
        )

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
