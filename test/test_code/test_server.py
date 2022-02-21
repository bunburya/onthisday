import unittest
from datetime import date

import pytz
import requests
from icalendar import Calendar
from test_code.test_utils import check_vevents_start_at, count_events


class ServerTestCase(unittest.TestCase):

    URL = 'http://127.0.0.1:8080/calendar'

    def test_01_test_defaults(self):
        r = requests.get(self.URL)
        cal = Calendar.from_ical(r.content)
        self.assertTrue(count_events(cal))
        self.assertTrue(check_vevents_start_at(cal, 9, 0))

    def test_02_custom_date_time(self):
        r = requests.get(self.URL + '?time=16:30&timezone=Europe:London&start=2020-04-05')
        cal = Calendar.from_ical(r.content)
        start = None
        end = None
        for e in cal.walk('vevent'):
            if start is None:
                start = e.get('dtstart').dt.date()
            end = e.get('dtstart').dt.date()
        self.assertEqual(date(2020, 4, 5), start)
        self.assertEqual(date(2021, 4, 4), end)
        self.assertTrue(check_vevents_start_at(cal, 16, 30), pytz.timezone('Europe/London'))

    def test_03_bad_timezone(self):
        r = requests.get(self.URL + '?timezone=BAD_TIMEZONE')
        self.assertEqual('Error parsing input: Bad timezone: BAD_TIMEZONE', r.text.strip())

    def test_04_bad_time(self):
        r = requests.get(self.URL + '?time=25:30')
        self.assertEqual('Error parsing input: The hour of the event must be between 0 and 23 (inclusive).',
                         r.text.strip())

