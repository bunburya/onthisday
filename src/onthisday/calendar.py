from datetime import date, timedelta, datetime
from typing import Optional, Generator, Union

from icalendar import Calendar, Event
from onthisday.db import DAO, InMemory


def date_range(start: date, end: date, step: timedelta = timedelta(days=1)) -> Generator[date, None, None]:
    """
    An iterator that returns every `step`th date from `start` to `end` (inclusive).

    :param start: Start date.
    :param end: End date.
    :param step: Step size.
    """
    if start > end:
        raise ValueError('Start date must be before end date.')
    _d = start
    while _d <= end:
        yield _d
        _d += step


def make_vevent(db: Union[DAO, InMemory], time: datetime, categories: Optional[dict[str, int]] = None) -> Event:
    """
    Create a single vEvent with one or more historical events.

    :param db: A :class:`DAO` or :class:`InMemory` object to retrieve historical events from the database.
    :param time: The date and time of the vEvent.
    :param categories: An optional dict mapping each event category name to the number of historical events from
        that category that should be included. Can be an OrderedDict if you want to enforce the order in which
        historical events should appear. If None, a single event from each category will be used for each day.
    :return: The :class:`Event` object.
    """
    events = {}
    month = time.strftime('%B')
    categories = categories or {
        'Births': 1,
        'Deaths': 1,
        'Holidays and observances': 1
    }
    for cat in categories:
        count = categories[cat]
        if count:
            events[cat] = db.get_random_events(month, time.day, cat, count)

    lines = []
    for cat in events:
        if not events[cat]:
            continue
        lines.append(cat)
        for m, d, c, y, desc in events[cat]:
            if y:
                lines.append(f'{y}: {desc}')
            else:
                lines.append(desc)
        lines.append('')

    event = Event()
    event.add('dtstart', time)
    event.add('summary', 'On This Day')
    event.add('description', '\n'.join(lines))
    return event


def make_calendar(db: Union[DAO, InMemory], start: date, end: date, time: tuple[int, int],
                  categories: Optional[dict[str, int]] = None) -> Calendar:
    """
    Create a calendar populated with random historical events, daily.

    :param db: A :class:`DAO` or :class:`InMemory` object to retrieve historical events from the database.
    :param start: The first date to include in the calendar.
    :param end: The last date to include in the calendar.
    :param time: A tuple representing the time at which the event should occur each day (hour, minute).
    :param categories: An optional dict mapping each event category name to the number of historical events from
        that category that should be included. Can be an OrderedDict if you want to enforce the order in which
        historical events should appear. If None, a single event from each category will be used for each day.
    :return: The :class:`Calendar` object.
    """

    hour, minute = time
    cal = Calendar()
    cal.add('prodid', '-//OnThisDay//bunburya.eu')
    cal.add('version', '0.1')

    for d in date_range(start, end):
        time = datetime(d.year, d.month, d.day, hour, minute)
        cal.add_component(make_vevent(db, time, categories))
    return cal
