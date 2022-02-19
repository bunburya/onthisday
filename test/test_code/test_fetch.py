import os
import unittest

from onthisday.db import DAO
from onthisday.get_data import parse_date_to_db, AlreadyScraped, ParsingError

TEST_DATA_DIR = 'test_data'
RUN_DIR = os.path.join(TEST_DATA_DIR, 'run')
if not os.path.exists(RUN_DIR):
    os.makedirs(RUN_DIR)
TEST_DB_FPATH = os.path.join(RUN_DIR, 'test.db')


class FetchDataTest(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB_FPATH):
            os.remove(TEST_DB_FPATH)
        self.db = DAO(TEST_DB_FPATH)

    def test_01_fetch_single_date(self):

        should_work = (
            # Should work
            ('January', 1),
            ('February', 29),
            ('June', 15),
            ('December', 31)
        )
        should_fail = (
            ('Smarch', 31),
            ('June', 43)
        )

        for m, d in should_work:
            self.assertGreater(parse_date_to_db(m, d, self.db), 0)
        for m, d in should_work:
            self.assertRaises(AlreadyScraped, parse_date_to_db, m, d, self.db)
        for m, d in should_fail:
            self.assertRaises(ParsingError, parse_date_to_db, m, d, self.db)



