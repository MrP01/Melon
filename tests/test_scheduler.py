import datetime

from melon.scheduler import AvailabilityManager, Task


class TestScheduler:
    def test_single_task_spread(self):
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(availability.spreadTasks([Task("1", 3.5, 1, "work")]))
        assert len(spread) == 1
        uid, slot = spread[0]
        assert uid == "1"
        assert slot.timestamp == startOfDay

    def test_multiple_task_spread(self):
        availability = AvailabilityManager()
        startOfDay = datetime.datetime.combine(datetime.date.today(), availability.startOfDay)
        spread = list(availability.spreadTasks([Task("1", 3.5, 1, "work"), Task("2", 2, 7, "home")]))
        assert len(spread) == 2
        assert spread[0][0] == "1"
        assert spread[1][0] == "2"
        assert spread[0][1].timestamp == startOfDay
        assert spread[1][1].timestamp == startOfDay + datetime.timedelta(hours=3.5)

    def test_simple_case(self):
        pass
