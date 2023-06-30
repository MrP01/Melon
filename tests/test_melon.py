"""Tests for the Melon object."""
from melon.melon import Melon


class TestMelon:
    """Test class containing multiple tests as methods."""

    def create_todos(self):
        """Not a test, this is to create some todos in the test database."""
        melon = Melon()
        melon.autoInit()
        melon.calendars["pytest"].createTodo("Hello").save()
        melon.calendars["pytest"].createTodo("Darkness").save()
        melon.calendars["pytest"].createTodo("My Old Friend").save()

    def test_init_store_and_load(self):
        """Initialises Melon, stores and loads."""
        melon = Melon()
        melon.fetch()
        melon.store()

        melon = Melon()
        melon.load()

    def test_sorting(self):
        """Sorts a list of Todo objects, which calls the underlying __lt__ function."""
        melon = Melon()
        melon.autoInit()
        allTasks = list(melon.allTasks())
        if not allTasks:
            self.create_todos()
            allTasks = list(melon.allTasks())
        allTasks.sort()
