#!/usr/bin/env python3

import argparse
import logging
import time
from typing import Union

from onthisday.calendar import make_calendar
from onthisday.common_data import MONTH_DAYS, date_from_yyyymmdd
from onthisday.db import DAO, InMemory
from onthisday.get_data import parse_all_to_db

logger = logging.getLogger(__name__)

def update(db: DAO, ns: argparse.Namespace):
    logger.info('Updating database.')
    parse_all_to_db(db)


CATEGORIES = {
    'death': 'Deaths',
    'birth': 'Births',
    'event': 'Events',
    'holiday': 'Holidays and observances'
}


def random(db: DAO, ns: argparse.Namespace):
    logger.info('Getting random events.')
    count = int(ns.count)
    cat = CATEGORIES.get(ns.category)
    month = ns.month
    date = ns.date
    for m, d, c, y, desc in db.get_random_events(month, date, cat, count):
        print(f'({d} {m}) {y} - {desc}')


def calendar(db: DAO, ns: argparse.Namespace):
    logger.info('Generating calendar.')
    category_counts = {
        'Deaths': ns.death,
        'Births': ns.birth,
        'Holidays and observances': ns.holiday
    }
    start = date_from_yyyymmdd(ns.start)
    end = date_from_yyyymmdd(ns.end)
    h_str, m_str = ns.time.split(':')
    cal = make_calendar(db, start, end, int(h_str), int(m_str), ns.timezone, categories=category_counts)
    print(cal.to_ical().decode())


def server(db: DAO, ns: argparse.Namespace):
    logger.info('Launching server.')
    from onthisday.app.download_calendar import run
    run(InMemory(db), ns.host, ns.port)


def test_calendar(db: Union[DAO, InMemory]) -> str:
    logger.info('Testing calendar.')
    return make_calendar(
        db,
        categories={
            'Deaths': 1,
            'Births': 1,
            'Holidays and observances': 1
        }
    ).to_ical().decode()

def timetest():
    print('DAO')
    print()
    print('Creating object...')
    start = time.time()
    db = DAO()
    end = time.time()
    print(f'Took {end - start} seconds.')
    print()
    print('Generating calendar...')
    start = time.time()
    test_calendar(db)
    end = time.time()
    print(f'Took {end - start} seconds.')
    print()
    print('InMemory')
    print()
    print('Creating object...')
    start = time.time()
    db = InMemory(DAO())
    end = time.time()
    print(f'Took {end - start} seconds.')
    print()
    print('Generating calendar...')
    start = time.time()
    test_calendar(db)
    end = time.time()
    print(f'Took {end - start} seconds.')


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', default=False)
parser.add_argument('--timetest', action='store_true', help='Test how long it takes to generate calendars using DAO vs '
                                                            'InMemory.')
parser.add_argument('--dbfile', help='Path to database file.', metavar='FILE', default=None)

subparsers = parser.add_subparsers()

update_parser = subparsers.add_parser('update', help='Fetch events from Wikipedia and update the database.')
update_parser.set_defaults(func=update)

random_parser = subparsers.add_parser('random', help='Print random events.')
random_parser.add_argument('--count', '-n', help='Number of results to return', type=int, default=1)
random_parser.add_argument('--category', '-c', help='Category of event', choices=CATEGORIES)
random_parser.add_argument('--month', '-m', help='Month to query', choices=MONTH_DAYS)
random_parser.add_argument('--date', '-d', help='Date to query', type=int)
random_parser.set_defaults(func=random)

cal_parser = subparsers.add_parser('calendar', help='Generate a vCalendar with random events.')
cal_parser.add_argument('--time', help='Time of daily event.', metavar='MM:SS', default='10:00')
cal_parser.add_argument('--start', help='Start date.', metavar='YYYYMMDD', default=None)
cal_parser.add_argument('--end', help='End date.', metavar='YYYYMMDD', default=None)
cal_parser.add_argument('--death', type=int, help='Number of deaths to include per day.', default=None, metavar='N')
cal_parser.add_argument('--birth', type=int, help='Number of births to include per day.', default=None, metavar='N')
cal_parser.add_argument('--holiday', type=int, help='Number of holidays/observances to include per day.', default=None,
                        metavar='N')
cal_parser.add_argument('--timezone', default='UTC', metavar='TZ',
                        help='Timezone for event time, eg, "UTC", "Europe/London", "America/New_York", etc.')
cal_parser.set_defaults(func=calendar)

serv_parser = subparsers.add_parser('server', help='Spin up a web app to serve calendars.')
serv_parser.add_argument('--host', help='Host to serve on.', default='localhost')
serv_parser.add_argument('--port', help='Port to listen on.', type=int, default=8080)
serv_parser.set_defaults(func=server)


if __name__ == '__main__':
    ns = parser.parse_args()
    # print(ns)
    if ns.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if ns.timetest:
        timetest()
        exit()

    if hasattr(ns, 'func'):
        db = DAO(ns.dbfile)
        ns.func(db, ns)
    else:
        parser.print_help()
