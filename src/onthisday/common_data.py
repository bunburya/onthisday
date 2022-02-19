from typing import Generator

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
