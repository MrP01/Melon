"""Tests for the scheduler algorithm."""
import datetime

from melon.scheduler import AvailabilityManager, Task


class TestAvailabilityManager:
    """Availability test class containing multiple tests as methods."""

    def test_single_task_spread(self):
        """Tests whether spreading a single task across the calendar works as expected."""
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(availability.spreadTasks([Task("1", 3.5, 1, "work")]))
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
                    Task("1", 3.5, 1, "work"),
                    Task("2", 2, 7, "home"),
                    Task("3", 11, 3, "work"),
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
