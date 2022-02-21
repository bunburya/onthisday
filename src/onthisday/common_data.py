from datetime import date, datetime
from typing import Generator, Optional, Any

MONTH_DAYS = {
    'January': 31,
    'February': 29,
    'March': 31,
    'April': 30,
    'May': 31,
    'June': 30,
    'July': 31,
    'August': 31,
    'September': 30,
    'October': 31,
    'November': 30,
    'December': 31
}
assert sum(MONTH_DAYS.values()) == 366

def iter_dates() -> Generator[tuple[str, int], None, None]:
    """
    Yields a tuple consisting of (month, date) for each date in the calendar.
    """
    for m in MONTH_DAYS:
        for d in range(MONTH_DAYS[m]):
            yield m, d + 1

EMPTY_EVENT_DICT = {
    'Events': [],
    'Births': [],
    'Deaths': [],
    'Holidays and observances': []
}

def date_from_yyyymmdd(s: Optional[str], fmt: str = '%Y%m%d') -> Optional[date]:
    """
    Generate a :class:`datetime.date` object from a string.

    :param s: Date string, or None.
    :param fmt: Format string, in a form compatible with :function:`datetime.datetime.strptime`.
    :param sep: Whether there is a character separating year
    :return: The date object, or None if `s` is None.
    """
    if s is None:
        return None
    else:
        return datetime.strptime(s, fmt).date()

def int_or_none(a: Optional[Any]) -> Optional[int]:
    """
    Convert value to an int, or return None if value is None.

    :param a: Value to convert.
    :return: Value as int, or None.
    """
    if a is None:
        return None
    else:
        return int(a)