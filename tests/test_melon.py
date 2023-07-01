"""Tests for the Melon object."""
import datetime
import random

import pytest

from melon.melon import Melon


class TestMelon:
    """Test class containing multiple tests as methods."""

    def create_todos(self, melon):
        """Not a test, this is to create some todos in the test database."""
        melon.calendars["pytest"].createTodo("Hello").save()
        melon.calendars["pytest"].createTodo("Darkness").save()
        melon.calendars["pytest"].createTodo("My Old Friend").save()

    def test_task_lookup(self):
        """Tests task look-up."""
        melon = Melon()
        melon.max_calendars = 3
        melon.autoInit()
        allTasks = list(melon.allTasks())
        if not allTasks:
            self.create_todos(melon)
        keyword = random.choice(allTasks).summary
        matches = list(melon.findTask(keyword))
        assert matches, keyword
        assert matches[0].uid is not None
        task = melon.getTask(matches[0].uid)
        assert task.uid == matches[0].uid
        with pytest.raises(ValueError):
            melon.getTask("u-i-d-that-definitely-does-not-exist")

    def test_init_store_and_load(self):
        """Initialises Melon, stores and loads."""
        melon = Melon()
        melon.max_calendars = 5
        melon.fetch()
        melon.store()

        melon = Melon()
        melon.load()

    def test_sorting(self):
        """Sorts a list of Todo objects, which calls the underlying __lt__ function."""
        melon = Melon()
        melon.max_calendars = 5
        melon.autoInit()
        allTasks = list(melon.allTasks())
        if not allTasks:
            self.create_todos(melon)
            allTasks = list(melon.allTasks())
        firstBestCalendar = next(iter(melon.calendars.values()))
        firstBestCalendar.createTodo()  # add an empty todo to be handled when sorting
        allTasks.sort()

    def test_todo_creation(self):
        """Tests the creation of a Todo with due date."""
        melon = Melon()
        melon.max_calendars = 3
        melon.autoInit()
        firstBestCalendar = next(iter(melon.calendars.values()))
        todo = firstBestCalendar.createTodo("New Todo")
        todo.dueDate = datetime.date.today()
        assert todo.dueDate == datetime.date.today()
        assert todo.dueTime is None
