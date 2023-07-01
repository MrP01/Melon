"""The scheduler algorithm"""
import math
import random
from datetime import date, datetime, time, timedelta
from typing import Iterable, Mapping

import tqdm

from .base import AbstractScheduler, Task, TimeSlot

INITIAL_TEMPERATURE = 0.2
SWEEP_EXPONENT = -1


class AvailabilityManager:
    """This class manages the user's availability in a calendar."""

    def __init__(self) -> None:
        """Initialises the availability manager according to defaults."""
        self.startOfDay = time(10, 0)  # start at 10am
        self.defaultDayLength = 14  # going all the way to 2am

    def startingSlot(self) -> TimeSlot:
        """Starting slot, starting at 10am today

        Returns:
            TimeSlot: the first working slot
        """
        return TimeSlot(datetime.combine(date.today(), self.startOfDay), self.defaultDayLength)

    def generateNextSlot(self, previous: TimeSlot) -> TimeSlot:
        """Following a daily schedule, returns the next possible working slot

        Args:
            previous (TimeSlot): the previous working slot

        Returns:
            TimeSlot: the next working slot
        """
        return TimeSlot(
            datetime.combine(previous.timestamp.date() + timedelta(days=1), self.startOfDay),
            self.defaultDayLength,
        )

    def spreadTasks(self, tasks: Iterable[Task]) -> Iterable[tuple[str, TimeSlot]]:
        """Spreads the given list of tasks across the available slots in the calendar, in order.

        Args:
            tasks (Iterable[Task]): list of tasks to schedule

        Yields:
            Iterator[tuple[str, TimeSlot]]: pairs of (UID, TimeSlot), returned in chronological order
        """
        slot = self.startingSlot()
        stamp = slot.timestamp
        for task in tasks:
            if task.duration > self.defaultDayLength:
                raise ValueError(
                    "You are trying to schedule a task longer than any working slot."
                    "Split it into smaller chunks! Automatic splitting is not supported."
                )
            taskDuration = timedelta(hours=task.duration)
            if stamp + taskDuration > slot.end:
                slot = self.generateNextSlot(slot)
                stamp = slot.timestamp
            yield (task.uid, TimeSlot(stamp, taskDuration.total_seconds() / 3600))
            stamp += taskDuration

    def isAvailable(self, timeslot: TimeSlot) -> bool:
        """Returns whether the given timeslot could fully fit within the designated timeframe.

        Args:
            timeslot (TimeSlot): the timeframe

        Returns:
            bool: whether the task fits
        """
        return False


class MCMCScheduler(AbstractScheduler):
    """MCMC class to schedule tasks to events in a calendar."""

    State = tuple[int, ...]  # using literal ellipsis to indicate a homogenous tuple of ints

    def __init__(self, tasks: list[Task]) -> None:
        """Initialises the MCMC scheduler, working on a set of pre-defined tasks.

        Args:
            tasks (list[Task]): the tasks to be scheduled
        """
        super().__init__(tasks)
        self.availability = AvailabilityManager()
        self.state = tuple(range(len(self.tasks)))  # initialise in order
        self.temperature = 1.0

    def permuteState(self) -> State:
        """Proposes a new state to use instead of the old state.

        Returns:
            State: the new state, a list of indices within self.tasks representing traversal order
        """
        newState = list(self.state)
        indexA = random.randrange(len(newState))
        indexB = random.randrange(len(newState))
        indexAValue = self.state[indexA]
        newState[indexA] = self.state[indexB]
        newState[indexB] = indexAValue
        return tuple(newState)

    def computeEnergy(self, state: State) -> float:
        """For the given state, compute an MCMC energy (the lower, the better)

        Args:
            state (State): state of the MCMC algorithm

        Returns:
            float: the energy / penalty for this state
        """
        spread = list(self.availability.spreadTasks(self.tasks[i] for i in state))
        totalTimePenalty = (spread[-1][1].end - spread[0][1].timestamp).total_seconds() / 3600
        priorityPenalty = sum(position * self.tasks[state[position]].priority for position in range(len(state)))
        allOnTime = True  # TODO: check with due date
        return totalTimePenalty + priorityPenalty

    def mcmcSweep(self):
        """Performs a full MCMC sweep"""
        energy = self.computeEnergy(self.state)
        for i in tqdm.tqdm(range(len(self.tasks) ** 2)):
            newState = self.permuteState()
            delta = self.computeEnergy(newState) - energy
            acceptanceProbability = min(math.exp(-delta / (energy * self.temperature)), 1)
            # print(f"New state with energy {energy + delta} (delta {delta}), accepted with {acceptanceProbability}.")
            if random.random() < acceptanceProbability:
                self.state = newState
                energy += delta

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Schedules the tasks using an MCMC procedure.

        Returns:
            Mapping[str, TimeSlot]: the resulting map of Tasks to TimeSlots
        """
        for k in range(1, 11):
            self.mcmcSweep()
            self.temperature = INITIAL_TEMPERATURE * k**SWEEP_EXPONENT
        print("Final State", self.state)
        return dict(self.availability.spreadTasks(self.tasks[i] for i in self.state))