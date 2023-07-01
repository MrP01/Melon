"""The scheduler algorithm"""
import dataclasses
from datetime import datetime, timedelta
from typing import Mapping


@dataclasses.dataclass
class Task:
    """Slim struct representing a task"""

    uid: str  # unique identifier of the task
    duration: float  # estimated, in hours
    priority: int  # between 1 and 9
    location: int  # number indicating the location, where 0 is "hybrid"


@dataclasses.dataclass
class TimeSlot:
    """Slim struct representing a time slot, so an event consisting of a start and end date."""

    timestamp: datetime
    duration: float  # in hours

    @property
    def timedelta(self) -> timedelta:
        """
        Returns:
            timedelta: the duration as a datetime.timedelta instance
        """
        return timedelta(hours=self.duration)

    @property
    def end(self) -> datetime:
        """
        Returns:
            datetime: the end timestamp of this time slot
        """
        return self.timestamp + self.timedelta


class AbstractScheduler:
    """Abstract Base Class (ABC) for schedulers."""

    def __init__(self, tasks: list[Task]) -> None:
        """Initialises the scheduler, working on a set of pre-defined tasks.

        Args:
            tasks (list[Task]): the tasks to be scheduled
        """
        self.tasks = tasks

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Schedules the tasks using an MCMC procedure.

        Returns:
            Mapping[str, TimeSlot]: the resulting map of Tasks to TimeSlots
        """
        raise NotImplementedError()