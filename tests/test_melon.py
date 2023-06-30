"""Tests for the Melon object."""
from melon.melon import Melon


class TestMelon:
    """Test class containing multiple tests as methods."""

    def test_init_store_and_load(self):
        """Initialises Melon, stores and loads."""
        melon = Melon()
        melon.init()
        melon.store()

        melon = Melon()
        melon.init()  # should have loaded instead of fetched
