"""Tests for the Melon object."""

import datetime
import os
import random
import re

import pytest

from melon.config import CONFIG_PATH, load_config
from melon.melon import Melon
from melon.scheduler.base import Task
from melon.scheduler.purepython import AvailabilityManager

MAX_CALENDARS = 3


class TestAvailabilityManager:
    """Availability test class containing multiple tests as methods."""

    def test_single_task_spread(self):
        """Tests whether spreading a single task across the calendar works as expected."""
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(availability.spreadTasks([Task("1", 3.5, 1, 1, None)]))
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
                    Task("1", 3.5, 1, 1, None),
                    Task("2", 2, 7, 2, None),
                    Task("3", 11, 3, 1, None),
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


class DoNotTestMelon:
    """Test class containing multiple tests as methods."""

    def create_todos(self, melon):
        """Not a test, this is to create some todos in the test database."""
        melon.calendars["pytest"].createTodo("Hello").save()
        melon.calendars["pytest"].createTodo("Darkness").save()
        melon.calendars["pytest"].createTodo("My Old Friend").save()

    def test_connect(self):
        """Tests connection to the configured server."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.connect()

    def test_config_load(self):
        """Tests loading of the configuration file."""
        backup = None
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                backup = f.read()

        validConfig = '[client]\nurl = "http://localhost:8000/dav/user/calendars/"'
        with open(CONFIG_PATH, "w") as f:
            f.write(validConfig)
        load_config()  # test loading it

        if backup is None:
            os.remove(CONFIG_PATH)
        else:
            with open(CONFIG_PATH, "w") as f:
                f.write(backup)

    def test_task_lookup(self):
        """Tests task search / look-up by keyword or UID."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.autoInit()
        allTasks = list(melon.allTasks())
        if not allTasks:
            self.create_todos(melon)
        allTasks = list(melon.allTasks())
        match = re.search(r"\b\w+\b", random.choice(allTasks).summary)
        keyword = match.group(0) if match else "Darkness"
        matches = list(melon.findTask(keyword))
        assert matches, keyword
        assert matches[0].uid is not None
        task = melon.getTask(matches[0].uid)
        assert task.uid == matches[0].uid
        with pytest.raises(ValueError):
            melon.getTask("u-i-d-that-definitely-does-not-exist")

    def test_init_store_and_load(self):
        """Initialises Melon, stores and loads."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.fetch()
        melon.store()

        melon = Melon()
        melon.load()

    def test_sorting(self):
        """Sorts a list of Todo objects, which calls the underlying __lt__ function."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.autoInit()
        allTasks = list(melon.allTasks())
        if not allTasks:
            self.create_todos(melon)
            allTasks = list(melon.allTasks())
        firstBestCalendar = next(iter(melon.calendars.values()))
        allTasks.append(firstBestCalendar.createTodo())  # add an empty todo to be handled when sorting
        allTasks.sort()

    def test_todo_creation(self):
        """Tests the creation of a Todo with due date."""
        melon = Melon(maxCalendars=MAX_CALENDARS)
        melon.autoInit()
        firstBestCalendar = next(iter(melon.calendars.values()))
        todo = firstBestCalendar.createTodo("New Todo")
        todo.dueDate = datetime.date.today()
        assert todo.dueDate == datetime.date.today()
        assert todo.dueTime is None
        assert todo.dueDateTime is not None
        assert isinstance(todo.summary, str)
        todo.summary = "Another summary"
        assert todo.summary == "Another summary"
        assert todo.isIncomplete()
        assert not todo.isComplete()
