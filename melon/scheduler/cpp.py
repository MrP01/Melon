"""The scheduler algorithm"""
import dataclasses
import pathlib
import sys
from datetime import date, datetime, timedelta
from typing import Mapping

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent / "build"))
import libcppscheduler

from .base import START_OF_DAY, AbstractScheduler, TimeSlot


class CppMCMCScheduler(AbstractScheduler):
    """Markov Chain Monte-Carlo Task Scheduler, implemented in Rust."""

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Runs the Rust implementation of the scheduler.

        Returns:
            Mapping[str, TimeSlot]: the resulting schedule
        """
        start = datetime.combine(date.today(), START_OF_DAY)  # equivalent to t = 0 for libcppscheduler
        result = libcppscheduler.schedule(list(map(dataclasses.astuple, self.tasks)))
        return {t[0]: TimeSlot(start + timedelta(hours=t[1]), t[2]) for t in result}
