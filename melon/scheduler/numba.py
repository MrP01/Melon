"""The scheduler algorithm"""
import dataclasses
import math
import random
from datetime import date, datetime, timedelta
from typing import Mapping, Sequence

import numba
from numba.typed.typedlist import List as NumbaList

from .base import DAY_LENGTH, INITIAL_TEMPERATURE, START_OF_DAY, SWEEP_EXPONENT, AbstractScheduler, TimeSlot

State = list[int]


@numba.njit()
def spreadTasks(tasks: Sequence[tuple[str, float, int, int]]) -> Sequence[tuple[str, float, float]]:
    """Spreads the given list of tasks across the available slots in the calendar, in order.

    Args:
        tasks (Sequence[Task]): list of tasks to schedule

    Yields:
        Iterator[tuple[str, TimeSlot]]: pairs of (UID, TimeSlot), returned in chronological order
    """
    order = []
    slot = (0.0, DAY_LENGTH)
    stamp = slot[0]
    for task in tasks:
        if task[1] > DAY_LENGTH:
            raise RuntimeError(
                "You are trying to schedule a task longer than any working slot."
                "Split it into smaller chunks! Automatic splitting is not supported."
            )
        if stamp + task[1] > slot[0] + slot[1]:
            slot = (slot[0] + 24.0, DAY_LENGTH)
            stamp = slot[0]
        order.append((task[0], stamp, task[1]))
        stamp += task[1]
    return order


@numba.njit()
def permuteState(state: State) -> State:
    """Proposes a new state to use instead of the old state.

    Returns:
        State: the new state, a list of indices within tasks representing traversal order
    """
    newState = state.copy()
    indexA = random.randrange(len(newState))
    indexB = random.randrange(len(newState))
    indexAValue = state[indexA]
    newState[indexA] = state[indexB]
    newState[indexB] = indexAValue
    return newState


@numba.njit()
def computeEnergy(tasks: Sequence[tuple[str, float, int, int]], state: State) -> float:
    """For the given state, compute an MCMC energy (the lower, the better)

    Args:
        state (State): state of the MCMC algorithm

    Returns:
        float: the energy / penalty for this state
    """
    spread = spreadTasks([tasks[i] for i in state])
    totalTimePenalty = spread[-1][1] + spread[-1][2] - spread[0][1]
    priorityPenalty = sum([position * tasks[state[position]][2] for position in range(len(state))])
    return totalTimePenalty + priorityPenalty


@numba.njit()
def mcmcSweep(tasks: Sequence[tuple[str, float, int, int]], initialState: State, temperature: float) -> State:
    """Performs a full MCMC sweep

    Args:
        tasks (Sequence[tuple[str, float, int, int]]): list of tasks
        initialState (State): initial ordering
        temperature (float): temperature for Simulated Annealing

    Returns:
        State: new state
    """
    state = initialState
    energy = computeEnergy(tasks, state)
    for i in range(len(tasks) ** 2):
        newState = permuteState(state)
        delta = computeEnergy(tasks, newState) - energy
        acceptanceProbability = min(math.exp(-delta / (energy * temperature)), 1)
        # print(f"New state with energy {energy + delta} (delta {delta}), accepted with {acceptanceProbability}.")
        if random.random() < acceptanceProbability:
            state = newState
            energy += delta
    return state


@numba.njit()
def schedule(tasks: Sequence[tuple[str, float, int, int]]) -> Sequence[tuple[str, float, float]]:
    """Schedules the given tasks in low-level representation into calendar.

    Args:
        tasks (Sequence[tuple[str, float, int, int]]): vector of tasks (uid, duration, priority, location)

    Returns:
        Sequence[tuple[str, float, float]]: vector of allocated timeslots (uid, timestamp, duration)
    """
    state = list(range(len(tasks)))
    for k in range(1, 11):
        temperature = INITIAL_TEMPERATURE * k**SWEEP_EXPONENT
        state = mcmcSweep(tasks, state, temperature)
    return spreadTasks([tasks[i] for i in state])


class NumbaMCMCScheduler(AbstractScheduler):
    """Markov Chain Monte-Carlo Task Scheduler, implemented in Python with numba speed-up."""

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Runs the Rust implementation of the scheduler.

        Returns:
            Mapping[str, TimeSlot]: the resulting schedule
        """
        start = datetime.combine(date.today(), START_OF_DAY)  # equivalent to t = 0
        result = schedule(NumbaList(map(dataclasses.astuple, self.tasks)))
        return {t[0]: TimeSlot(start + timedelta(hours=t[1]), t[2]) for t in result}
