"""The scheduler algorithm"""
import dataclasses
from datetime import datetime, timedelta
from typing import Iterable, Mapping

import numba
from numba.typed.typedlist import List as NumbaList

from .base import AbstractScheduler, TimeSlot


@numba.njit()
def schedule(tasks: Iterable[tuple[str, float, int, int]]) -> Iterable[tuple[str, float, float]]:
    """Schedules the given tasks in low-level representation into calendar.

    Args:
        tasks (Iterable[tuple[str, float, int, int]]): vector of tasks (uid, duration, priority, location)

    Returns:
        Iterable[tuple[str, float, float]]: vector of allocated timeslots (uid, timestamp, duration)
    """
    results = []
    for task in tasks:
        results.append((task[0], 0.0, task[1]))
    return results


class NumbaMCMCScheduler(AbstractScheduler):
    """Markov Chain Monte-Carlo Task Scheduler, implemented in Python with numba speed-up."""

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Runs the Rust implementation of the scheduler.

        Returns:
            Mapping[str, TimeSlot]: the resulting schedule
        """
        start = datetime.now()  # equivalent to t = 0 for libscheduler
        result = schedule(NumbaList(map(dataclasses.astuple, self.tasks)))
        return {t[0]: TimeSlot(start + timedelta(hours=t[1]), t[2]) for t in result}
