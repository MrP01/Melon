"""Tests for the scheduler algorithm."""
import datetime
import pathlib
import tempfile

import pytest

from melon.melon import Melon
from melon.scheduler import AbstractScheduler, AvailabilityManager, MCMCScheduler, RustyMCMCScheduler, Task


class TestAvailabilityManager:
    """Availability test class containing multiple tests as methods."""

    def test_single_task_spread(self):
        """Tests whether spreading a single task across the calendar works as expected."""
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(availability.spreadTasks([Task("1", 3.5, 1, 1)]))
        assert len(spread) == 1
        uid, slot = spread[0]
        assert uid == "1"
        assert slot.timestamp == startOfDay

    def test_multiple_task_spread(self):
        """Tests whether spreading multiple tasks across two days works as expected,
        scheduling two tasks after one another and the third one for the next day.
        """
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(
            availability.spreadTasks(
                [
                    Task("1", 3.5, 1, 1),
                    Task("2", 2, 7, 2),
                    Task("3", 11, 3, 1),
                ]
            )
        )
        assert len(spread) == 3
        assert spread[0][0] == "1"
        assert spread[1][0] == "2"
        assert spread[2][0] == "3"
        assert spread[0][1].timestamp == startOfDay
        assert spread[1][1].timestamp == startOfDay + datetime.timedelta(hours=3.5)
        assert spread[2][1].timestamp == startOfDay + datetime.timedelta(days=1)


class TestScheduler:
    """Class that tests various functionality of the schedulers."""

    @pytest.mark.parametrize("Scheduler", (MCMCScheduler, RustyMCMCScheduler))
    def test_priority_scheduling(self, Scheduler: type[AbstractScheduler]):
        """Sees whether the scheduler puts high-priority tasks first."""
        scheduler = Scheduler([Task("1", 3.5, 1, 1), Task("2", 2, 7, 2), Task("3", 11, 3, 1), Task("4", 2, 9, 0)])
        result = scheduler.schedule()
        assert len(result) == len(scheduler.tasks)

    @pytest.mark.parametrize("Scheduler", (MCMCScheduler, RustyMCMCScheduler))
    def test_real_data_scheduling(self, Scheduler: type[AbstractScheduler]):
        """Schedules based on what autoInit() gives us."""
        melon = Melon()
        melon.max_calendars = 3
        melon.autoInit()
        scheduler = Scheduler(melon.tasksToSchedule())
        result = scheduler.schedule()
        assert len(result) == len(scheduler.tasks)

    @pytest.mark.parametrize("Scheduler", (MCMCScheduler, RustyMCMCScheduler))
    def test_schedule_and_export(self, Scheduler: type[AbstractScheduler]):
        """Runs scheduleAllAndExport() to schedule and create an ICS file."""
        melon = Melon()
        melon.max_calendars = 3
        melon.autoInit()
        outFolder = pathlib.Path(tempfile.gettempdir())
        melon.scheduleAllAndExport(str(outFolder / "schedule.ics"), Scheduler=Scheduler)
