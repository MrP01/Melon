"""Tests for the scheduler algorithm."""
import datetime
import pathlib
import random
import tempfile
from typing import Mapping

import pytest

from melon.melon import Melon
from melon.scheduler.base import START_OF_DAY, AbstractScheduler, Task, TimeSlot, generateDemoTasks
from melon.scheduler.cpp import CppMCMCScheduler
from melon.scheduler.numba import NumbaMCMCScheduler
from melon.scheduler.purepython import MCMCScheduler
from melon.scheduler.rust import RustyMCMCScheduler
from melon.visualise import plotConvergence, radarChart

MAX_CALENDARS = 3
ALL_IMPLEMENTATIONS = (MCMCScheduler, RustyMCMCScheduler, NumbaMCMCScheduler, CppMCMCScheduler)


class TestScheduler:
    """Class that tests various functionality of the schedulers."""

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def test_length(self, Scheduler: type[AbstractScheduler]):
        """Tests whether all task were scheduled."""
        scheduler = Scheduler(generateDemoTasks())
        result = scheduler.schedule()
        assert isinstance(result, Mapping)
        assert len(result) == len(scheduler.tasks)

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def test_correct_format(self, Scheduler: type[AbstractScheduler]):
        """Checks the output format of each scheduler in detail."""
        start = datetime.datetime.combine(datetime.date.today(), START_OF_DAY)
        scheduler = Scheduler(generateDemoTasks())
        taskMap = scheduler.uidTaskMap()
        result = scheduler.schedule()
        assert isinstance(result, Mapping)
        for uid, slot in result.items():
            assert isinstance(uid, str)
            assert len(uid) > 0
            assert uid in taskMap.keys()
            assert isinstance(slot, TimeSlot)
            assert isinstance(slot.timestamp, datetime.datetime)
            assert slot.timestamp >= start
            assert isinstance(slot.duration, float)
            assert slot.duration > 0
            assert slot.duration == taskMap[uid].duration

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def test_priority_scheduling(self, Scheduler: type[AbstractScheduler]):
        """Sees whether the scheduler puts high-priority tasks first."""
        tasks = [Task(str(i), 1.0, i, 0, None) for i in range(1, 5)]
        random.shuffle(tasks)
        scheduler = Scheduler(tasks)
        result = scheduler.schedule()
        assert len(result) == len(scheduler.tasks)
        ordered = sorted(scheduler.tasks, key=lambda t: t.priority, reverse=True)
        uidList = [uid for uid in sorted(result.keys(), key=lambda uid: result[uid].timestamp)]
        expectedUidList = [t.uid for t in ordered]
        assert uidList == expectedUidList

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def test_task_too_long(self, Scheduler: type[AbstractScheduler]):
        """Tests whether tasks are too long."""
        scheduler = Scheduler([Task("1", 3.5, 1, 1, None), Task("2", 200.0, 7, 2, None)])
        with pytest.raises((RuntimeError, SystemError)):
            scheduler.schedule()

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def do_not_test_real_data_scheduling(self, Scheduler: type[AbstractScheduler]):
        """Schedules based on what autoInit() gives us."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.autoInit()
        scheduler = Scheduler(melon.tasksToSchedule())
        result = scheduler.schedule()
        assert len(result) == len(scheduler.tasks)

    @pytest.mark.parametrize("Scheduler", ALL_IMPLEMENTATIONS)
    def do_not_test_schedule_and_export(self, Scheduler: type[AbstractScheduler]):
        """Runs scheduleAllAndExport() to schedule and create an ICS file."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.autoInit()
        outFolder = pathlib.Path(tempfile.gettempdir())
        melon.scheduleAllAndExport(str(outFolder / "schedule.ics"), Scheduler=Scheduler)

    @pytest.mark.filterwarnings("ignore:Enum:DeprecationWarning")
    def test_purepython_convergence_plot(self):
        """Plots the MCMC convergence."""
        import numpy as np

        scheduler = MCMCScheduler(generateDemoTasks())
        scheduler.schedule()
        plotConvergence(np.array([scheduler.energyLog]), ["label"], filename=None)

    @pytest.mark.filterwarnings("ignore:Enum:DeprecationWarning")
    def test_radar_chart(self):
        """Plots the resulting radar chart."""
        radarChart((0.3, 0.5, 0.8), "Chart Title")
