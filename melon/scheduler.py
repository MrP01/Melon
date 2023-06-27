"""The scheduler algorithm"""
import collections
import datetime
import math
import random
from typing import Iterable, Mapping

Task = collections.namedtuple("Task", ["uid", "duration", "priority", "location"])
TimeSlot = collections.namedtuple("TimeSlot", ["timestamp", "duration"])


class AvailabilityManager:
    """This class manages the user's availability in a calendar."""

    def __init__(self) -> None:
        """Initialises the availability manager according to defaults."""
        self.startOfDay = datetime.time(10, 0)
        self.endOfDay = datetime.time(23, 59)

    def spreadTasks(self, tasks: Iterable[Task]) -> Iterable[tuple[str, TimeSlot]]:
        """Spreads the given list of tasks across the available slots in the calendar, in order.

        Args:
            tasks (Iterable[Task]): list of tasks to schedule

        Yields:
            Iterator[Iterable[tuple[str, TimeSlot]]]: pairs of (UID, TimeSlot), returned in chronological order
        """
        stamp = datetime.datetime.now()
        for task in tasks:
            if (stamp + task.duration).time() > self.endOfDay:
                stamp = (stamp + datetime.timedelta(days=1)).replace(
                    hour=self.startOfDay.hour,
                    minute=self.startOfDay.minute,
                )
            yield (task.uid, TimeSlot(stamp, task.duration))

    def isAvailable(self, timeslot: TimeSlot) -> bool:
        """Returns whether the given timeslot could fully fit within the designated timeframe.

        Args:
            timeslot (TimeSlot): the timeframe

        Returns:
            bool: whether the task fits
        """
        return False


class MCMCScheduler:
    """MCMC class to schedule tasks to events in a calendar."""

    def __init__(self, tasks: list[Task]) -> None:
        """Initialises the MCMC scheduler, working on a set of pre-defined tasks.

        Args:
            tasks (list[Task]): the tasks to be scheduled
        """
        self.tasks = tasks
        self.availability = AvailabilityManager()
        self.state = tuple(range(len(self.tasks)))  # initialise in order
        self.temperature = 1.0

    def permuteState(self) -> tuple[int]:
        """Proposes a new state to use instead of the old state.

        Returns:
            tuple[int]: the new state, a list of indices within self.tasks representing traversal order
        """
        return (1, 2, 3)

    def computeEnergy(self, state: tuple[int]) -> float:
        """For the given state, compute an MCMC energy (the lower, the better)

        Args:
            state (tuple[int]): the state of the MCMC algorithm

        Returns:
            float: the energy
        """
        spread = dict(self.availability.spreadTasks([self.tasks[i] for i in state]))
        allOnTime = True  # TODO: check with due date
        return max(slot.timestamp + slot.duration for uid, slot in spread.items())

    def mcmcSweep(self):
        """Performs a full MCMC sweep"""
        energy = self.computeEnergy(self.state)
        for i in range(100):
            newState = self.permuteState()
            delta = self.computeEnergy(newState) - energy
            acceptanceProbability = min(math.exp(-delta / self.temperature), 1)
            if random.random() < acceptanceProbability:
                self.state = newState
                energy += delta

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Schedules the tasks using an MCMC procedure.

        Returns:
            Mapping[str, TimeSlot]: the resulting map of Tasks to TimeSlots
        """
        return {"uid-123": TimeSlot()}
