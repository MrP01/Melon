"""The scheduler algorithm"""
import dataclasses
import random
from datetime import datetime, time, timedelta
from typing import Mapping

START_OF_DAY = time(10, 0)
DAY_LENGTH = 14
INITIAL_TEMPERATURE = 0.4
SWEEP_EXPONENT = -2.0


@dataclasses.dataclass
class Task:
    """Slim struct representing a task"""

    uid: str  # unique identifier of the task
    duration: float  # estimated, in hours
    priority: int  # between 1 and 9
    location: int  # number indicating the location, where 0 is "hybrid"
    due: datetime | None  # when the task is due

    def asTuple(self, start: datetime) -> tuple[str, float, int, int, float]:
        """Returns a low-level representation of this instance.

        Args:
            start (datetime): Start time reference for the due date

        Returns:
            tuple[str, float, int, int, float]: low-level representation (uid, duration, priority, location, due).
                due is 0 if there is no due date.
        """
        return (
            self.uid,
            self.duration,
            self.priority,
            self.location,
            (self.due - start).total_seconds() / 3600 if self.due is not None else 0,
        )


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

    def uidTaskMap(self) -> Mapping[str, Task]:
        """Generates a dictionary for task lookup by UID.

        Returns:
            Mapping[str, Task]: the dictionary keyed by UID of each task.
        """
        return {task.uid: task for task in self.tasks}

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Schedules the tasks using an MCMC procedure.

        Returns:
            Mapping[str, TimeSlot]: the resulting map of Tasks to TimeSlots
        """
        raise NotImplementedError()


def generateDemoTasks() -> list[Task]:
    """Generates a fixed set of demo tasks.

    Returns:
        list[Task]: the generated list of tasks
    """
    now = datetime.now()
    return [
        Task("1", 3.5, 1, 1, now + timedelta(hours=3)),
        Task("2", 2.0, 7, 2, None),
        Task("3", 11.0, 3, 1, now + timedelta(hours=22)),
        Task("4", 2.0, 9, 0, now + timedelta(hours=100)),
        Task("5", 4.0, 5, 1, None),
    ]


def generateManyDemoTasks(N: int, proportionOfDueDates: float = 0.5) -> list[Task]:
    """Generates a larger set of randomly generated demo tasks.

    Args:
        N (int): Number of tasks to be generated
        proportionOfDueDates (float, optional): what percentage (from 0 to 1) of tasks should have a due date.
                                                Defaults to 0.5.

    Returns:
        list[Task]: the list of tasks
    """
    now = datetime.now()
    return [
        Task(
            uid=str(i),
            duration=random.randint(1, 2 * DAY_LENGTH) / 2,
            priority=random.randint(1, 9),
            location=random.randint(0, 2),
            due=now + timedelta(hours=random.randint(10, N * 5)) if random.random() < proportionOfDueDates else None,
        )
        for i in range(N)
    ]
