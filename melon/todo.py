import datetime
from typing import Literal

import caldav
import caldav.lib.url
import vobject


class Todo(caldav.Todo):
    vobject_instance: vobject.base.Component

    def __init__(self, todo: caldav.Todo, calendarName: str):
        """A copy constructor"""
        super().__init__(todo.client, todo.url, todo.data, todo.parent, todo.id, todo.props)
        self.calendarName = calendarName

    @property
    def vtodo(self) -> vobject.base.Component:
        return self.vobject_instance.contents["vtodo"][0]  # type: ignore

    @property
    def summary(self) -> str:
        return self.vtodo.contents["summary"][0].value  # type: ignore

    @summary.setter
    def summary(self, value: str):
        self.vtodo.contents["summary"][0].value = value  # type: ignore

    @property
    def dueDate(self) -> datetime.datetime | None:
        if "due" in self.vtodo.contents:
            due = self.vtodo.contents["due"][0].value  # type: ignore
            if isinstance(due, datetime.date):
                return datetime.datetime.combine(due, datetime.time())
            return due

    @property
    def uid(self) -> str | None:
        try:
            return self.vtodo.contents["uid"][0].value  # type: ignore
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
