from typing import Iterable

def schedule(tasks: Iterable[tuple[str, float, int, int]]) -> Iterable[tuple[str, float, float]]:
    """Schedules the given tasks in low-level representation into calendar.

    Args:
        tasks (Iterable[tuple[str, float, int, int]]): vector of tasks (uid, duration, priority, location)

    Returns:
        Iterable[tuple[str, float, float]]: vector of allocated timeslots (uid, timestamp, duration)
    """
