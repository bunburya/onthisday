import unittest
from datetime import date

import pytz
from onthisday.calendar import make_calendar
from onthisday.db import DAO
from test_code.test_utils import is_valid_cal, count_events, check_vevents_start_at


class CalendarTestCase(unittest.TestCase):

    DB = DAO()

    def test_00_make_calendar(self):
        leap_start = date(2020, 1, 1)
        nonleap_start = date(2021, 1, 1)
        leap_cal = make_calendar(self.DB, start=leap_start)
        self.assertEqual(366, count_events(leap_cal))
        self.assertTrue(check_vevents_start_at(leap_cal, 9, 0))

        nonleap_cal = make_calendar(self.DB, start=nonleap_start)
        self.assertEqual(365, count_events(nonleap_cal))
        self.assertTrue(check_vevents_start_at(nonleap_cal, 9, 0))

    def test_01_with_defaults(self):
        cal = make_calendar(self.DB)
        self.assertTrue(is_valid_cal(cal.to_ical().decode()))

    def test_02_with_tz(self):
        cal = make_calendar(self.DB, tz=pytz.timezone('Europe/London'))
        self.assertTrue(is_valid_cal(cal.to_ical().decode()))