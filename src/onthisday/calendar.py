from datetime import date, timedelta, datetime
from typing import Optional, Generator, Union

import pytz
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


def make_vevent(db: Union[DAO, InMemory], time: datetime,
                categories: Optional[dict[str, int]] = None) -> Event:
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
        'Events': 1,
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


def make_calendar(db: Union[DAO, InMemory], start: date = None, end: date = None, hour: int = 9, minute: int = 0,
                  tz: pytz.tzinfo.BaseTzInfo = pytz.UTC, categories: Optional[dict[str, int]] = None) -> Calendar:
    """
    Create a calendar populated with random historical events, daily.

    :param db: A :class:`DAO` or :class:`InMemory` object to retrieve historical events from the database.
    :param start: The first date to include in the calendar. If None, use today's date.
    :param end: The last date to include in the calendar. If None, use one year from `start`.
    :param hour: The hour at which to schedule each "event".
    :param minute: The minute (past `hour`) at which to schedule each "event".
    :param tz: The timezone of the event time.
    :param categories: An optional dict mapping each event category name to the number of historical events from
        that category that should be included. Can be an OrderedDict if you want to enforce the order in which
        historical events should appear. If None, a single event from each category will be used for each day.
    :return: The :class:`Calendar` object.
    """

    if start is None:
        start = date.today()

    if end is None:
        end = date(start.year+1, start.month, start.day) - timedelta(days=1)

    if categories is None:
        categories = {
            'Births': 1,
            'Deaths': 1,
            'Events': 1,
            'Holidays and observances': 1
        }

    if set(categories.values()) == {None}:
        for c in categories:
            categories[c] = 1

    cal = Calendar()
    cal.add('prodid', '-//OnThisDay//bunburya.eu')
    cal.add('version', '0.1')

    for d in date_range(start, end):
        time = datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
        cal.add_component(make_vevent(db, time, categories))
    return cal
