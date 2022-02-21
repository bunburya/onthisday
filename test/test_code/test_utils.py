"""
Various helper functions for performing tests.
"""
from typing import Optional

import pytz
from icalendar import Calendar, Event


def is_valid_cal(s: str) -> bool:
    """
    Test whether given string is valid iCalendar data.
    :param s: String to test.
    :return: Whether string is valid iCalendar data.
    """
    try:
        Calendar.from_ical(s)
        return True
    except ValueError:
        return False


def count_events(cal: Calendar, evt_type: str = 'vevent') -> int:
    """
    Count the number of events in the given calendar.

    :param cal: The calendar to search.
    :param evt_type: What type of event to count.
    :return: Number of events.
    """
    count = 0
    for evt in cal.walk(evt_type):
        count += 1
    return count


def check_vevents_start_at(cal: Calendar, hour: int, minute: int, tz: Optional[pytz.BaseTzInfo] = None) -> bool:
    """
    Verify that all vEvents in the given calendar begin at the specified time.

    """

    for evt in cal.walk('vevent'):
        start = evt['dtstart']
        if (start is None) or (start.dt is None) or (start.dt.hour != hour) or (start.dt.minute != minute):
            return False
        if (tz is not None) and (tz != start.dt.tzinfo):
            return False
    return True
