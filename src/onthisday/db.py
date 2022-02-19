import os
import sqlite3
from random import sample
from typing import Optional, Any

import appdirs
from onthisday.common_data import MONTH_DAYS, EMPTY_EVENT_DICT, iter_dates


def build_select(table: str, *cols: str, **criteria: str) -> str:
    """
    Build an SQL SELECT query based on the given parameters.

    NOTE: Neither `table` nor `cols` are escaped or otherwise sanitised, so only pass trusted arguments.

    :param table: The name of the table to query.
    :param cols: Names of the columns to return.
    :param criteria: Keyword arguments specifying the criteria to use, ie, X and Y in "WHERE X = Y".
    :return: The full SELECT query.
    """
    col_names = ', '.join(cols)
    query = f'SELECT {col_names} FROM {table}'
    if criteria:
        criteria_parts = []
        for k in criteria:
            criteria_parts.append(f'{k} = "{criteria[k]}"')
        criteria_str = ' AND '.join(criteria_parts)
        query += f' WHERE {criteria_str}'
    return query


def validate_criteria(**kwargs: Any) -> dict[str, Any]:
    """
    Validate the given keyword arguments, by converting to the appropriate types, doing some other sanity checks and
    raising errors as appropriate.

    :param kwargs: Keyword arguments to validate.
    :return: A dict of converted, validated keywords.
    """
    valid = {}
    for k in kwargs:
        v = kwargs[k]
        if k == 'month':
            month = v.title()
            if month not in MONTH_DAYS:
                raise ValueError(f'Invalid month: "{month}".')
            valid[k] = month
        elif k == 'date':
            try:
                date = int(v)
            except ValueError:
                raise ValueError(f'Date must be an integer (not "{v}").')
            if date < 1:
                raise ValueError(f'Invalid date: "{date}".')
            month = kwargs.get('month', '').title()
            if month:
                if date > MONTH_DAYS[month]:
                    raise ValueError(f'Invalid date for month {month}: "{date}".')
            valid[k] = date
        elif k == 'event_category':
            if v not in EMPTY_EVENT_DICT:
                raise ValueError(f'Invalid category: "{v}".')
            valid[k] = v
    return valid


def get_event_query(month: Optional[str] = None, date: Optional[int] = None,
                    event_category: Optional[str] = None) -> str:
    """
    Create an SQL query to get events matching the given criteria.

    :param month: The month of the event.
    :param date: The date (day of the month) of the event.
    :param event_category: The event category ("Births", "Deaths", "Events", "Holidays and observances").
    :return: The SQL query.
    """
    criteria = {}
    if month is not None:
        criteria['month'] = month
    if date is not None:
        criteria['date'] = date
    if event_category is not None:
        criteria['event_category'] = event_category
    criteria = validate_criteria(**criteria)
    return build_select('events', 'month', 'date', 'event_category', 'year', 'description', **criteria)


class DAO:
    """
    Data access object for the database used to store event information.

    :param db_fpath: Path to the database file. If none specified, a sane default is selected.
    """

    OTD_EVENT_SCHEMA = """
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL COLLATE NOCASE,
            date INTEGER NOT NULL,
            rev_id INTEGER NOT NULL,
            event_category TEXT NOT NULL COLLATE NOCASE,
            year TEXT NOT NULL COLLATE NOCASE,
            description TEXT NOT NULL
        )
    """

    OTD_REVISIONS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS revisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL COLLATE NOCASE,
            date INTEGER NOT NULL,
            rev_id INTEGER NOT NULL,
            UNIQUE(month, date)
        )
        
    """

    INSERT_OTD_EVENT = """
        INSERT INTO events(month, date, rev_id, event_category, year, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    INSERT_OTD_REVISION = """
        INSERT OR REPLACE INTO revisions(month, date, rev_id) VALUES (?, ?, ?)
    """

    GET_REVISION = """
        SELECT rev_id FROM revisions WHERE month = ? AND date = ?
    """

    def __init__(self, db_fpath: Optional[str] = None):
        if db_fpath is None:
            db_fpath = self.get_default_db_fpath()
        self.db_fpath = db_fpath
        self.db = sqlite3.connect(db_fpath)
        self.create_tables()

    def get_default_db_fpath(self, make_dirs: bool = True):
        """
        Get the default path to the database file.

        :param make_dirs: If True, automatically create any directories that are needed to store the database file.
        :return: The path to the database file (the file itself is not guaranteed to exist).
        """

        app_data_dir = appdirs.user_data_dir('onthisday')
        db_dir = os.path.join(app_data_dir, 'db')
        if make_dirs and (not os.path.exists(db_dir)):
            os.makedirs(db_dir)
        return os.path.join(db_dir, 'onthisday.db')

    def create_tables(self):
        self.db.execute(self.OTD_EVENT_SCHEMA)
        self.db.execute(self.OTD_REVISIONS_SCHEMA)

    def insert_events(self, month: str, date: int, rev_id: int, event: dict[str, list[tuple[str, str]]]) -> int:
        """
        Insert the given events into the relevant database table.

        :param month: The month of the event.
        :param date: The date (day of month) of the event.
        :param rev_id: The revision ID of the Wikipedia page where we found the event.
        :param event: A dict containing the event information. NB: The dict is modified in the process.
        :return: The number of events inserted.
        """
        counter = 0
        for evt_cat in event:
            for year, desc in event[evt_cat]:
                self.db.execute(self.INSERT_OTD_EVENT, (month, date, rev_id, evt_cat, year, desc))
                counter += 1
        return counter

    def insert_revision(self, month: str, date: int, rev_id: int):
        """
        Insert a revision ID for a particular date into the relevant database table.
        :param month: Month.
        :param date: Date (day of month).
        :param rev_id: Revision ID.
        """
        self.db.execute(self.INSERT_OTD_REVISION, (month, date, rev_id))

    def get_revision(self, month: str, date: int) -> str:
        """
        Get the latest revision ID for a particular date.
        :param month: Month.
        :param date: Date (day of month).
        :return: Revision ID.
        """
        result = self.db.execute(self.GET_REVISION, (month, date)).fetchone()
        if result is not None:
            result = result[0]
        return result

    def get_random_events(self, month: Optional[str] = None, date: Optional[int] = None,
                          event_category: Optional[str] = None, count: int = 1) -> list[tuple[str, str]]:
        """
        Return `n` random events for the given date, based on the given criteria.

        NOTE: This function is more flexible, but slower, than the equivalent method of the :class:`InMemory` class. For
        generating calendars, use that method instead.

        :param month: The month of the event. If None, a random month will be chosen.
        :param date: The date (day of the month) of the event. If None, a random date will be chosen.
        :param event_category: The event category ("Births", "Deaths", "Events", "Holidays and observances"). If None,
            a random category will be chosen.
        :param count: The number of events to return.
        :return: A list, of length `n`, of events (as tuples comprised of year + description).
        """
        try:
            count = int(count)
        except ValueError:
            raise ValueError(f'Count must be an integer greater than 0 (not {count}).')
        if count < 1:
            raise ValueError(f'Count must be an integer greater than 0 (not {count}).')
        base_query = get_event_query(month, date, event_category)
        full_query = f'{base_query} ORDER BY RANDOM() LIMIT {int(count)}'
        return self.db.execute(full_query).fetchall()

    def get_all_events(self, month: Optional[str] = None, date: Optional[int] = None,
                       event_category: Optional[str] = None) -> list[tuple[str, str]]:
        """
        Return all events matching the given criteria.

        :param month: The month of the event.
        :param date: The date (day of the month) of the event.
        :param event_category: The event category ("Births", "Deaths", "Events", "Holidays and observances").
        :return: A list, of length `n`, of events (as tuples comprised of year + description).
        """
        return self.db.execute(get_event_query(month, date, event_category)).fetchall()

    def commit(self):
        self.db.commit()


class InMemory:
    """
    Holds all events in-memory for quick retrieval.

    :param db: The :class:`DAO` object for loading events from the database.
    """

    def __init__(self, db: DAO):
        self.db = db
        self.events = {}
        for m in MONTH_DAYS:
            self.events[m] = {}
            for d in range(1, MONTH_DAYS[m]+1):
                self.events[m][d] = {}
                for c in EMPTY_EVENT_DICT:
                    self.events[m][d][c] = db.get_all_events(m, d, c)

    def get_random_events(self, month: str, date: int, event_category: str, count: int = 1) -> list[tuple[str, str]]:
        """
        Return `n` random events for the given date, based on the given criteria.

        :param month: The month of the event.
        :param date: The date (day of the month) of the event.
        :param event_category: The event category ("Births", "Deaths", "Events", "Holidays and observances").
        :param count: The number of events to return.
        :return: A list, of length `n`, of events (as tuples comprised of year + description).
        """
        try:
            count = int(count)
        except ValueError:
            raise ValueError(f'Count must be an integer greater than 0 (not {count}).')
        if count < 1:
            raise ValueError(f'Count must be an integer greater than 0 (not {count}).')

        try:
            return sample(self.events[month][date][event_category], count)
        except ValueError:
            return []
