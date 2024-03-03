"""The scheduler algorithm"""

import logging
import pathlib
import sys
from datetime import date, datetime, timedelta
from typing import Mapping

try:
    from melon.scheduler import libscheduler
except ImportError:
    importPath = str(pathlib.Path(__file__).resolve().parent.parent.parent / "target" / "release")
    logging.info(f"Could not find packaged .so file, falling back to {importPath} directory")
    sys.path.append(importPath)
    import libscheduler

from .base import START_OF_DAY, AbstractScheduler, TimeSlot


class RustyMCMCScheduler(AbstractScheduler):
    """Markov Chain Monte-Carlo Task Scheduler, implemented in Rust."""

    def schedule(self) -> Mapping[str, TimeSlot]:
        """Runs the Rust implementation of the scheduler.

        Returns:
            Mapping[str, TimeSlot]: the resulting schedule
        """
        start = datetime.combine(date.today(), START_OF_DAY)  # equivalent to t = 0 for libscheduler
        result = libscheduler.schedule([task.asTuple(start) for task in self.tasks])
        return {t[0]: TimeSlot(start + timedelta(hours=t[1]), t[2]) for t in result}
