import logging
import re
from copy import deepcopy
from typing import Union, Generator

import wikitextparser
from mediawiki import MediaWiki
from onthisday.common_data import MONTH_DAYS, EMPTY_EVENT_DICT, iter_dates
from onthisday.db import DAO

logger = logging.getLogger(__name__)

class ParsingError(Exception):
    """
    Error when parsing the content received from Wikipedia.
    """
    pass


class AlreadyScraped(Exception):
    """
    We have already parsed and saved the latest revision of this page, so don't parse again.
    """
    pass


EVENT_RE = re.compile(r"^\*\s*(\d+)\s*–\s*(.+)$")
H1_RE = re.compile("^==([^=]+)==$")
H2_RE = re.compile(r"^===([^=]+)===$")


def empty_events_dict() -> dict[str, list[tuple[str, str]]]:
    return deepcopy(EMPTY_EVENT_DICT)


def parse_holidays(lines: list[str], sep: str = ' - ') -> list[tuple[str, str]]:
    """
    Parse the "Holidays and observances" section of the article.

    The main thing this function does is flatten nested lists by linking together the top-level and sub-list entries.
    Eg, the following list:

    ```
    *Christian feast day:
    **Alphonsus Rodriguez
    **Ampliatus
    **Begu
    ```

    would become (assuming `: ` was provided as the `sep` argument):

    ```
    Christian feast day: Alphonsus Rodrigues
    Christian feast day: Ampliatus
    Christian feast day: Begu
    ```

    :param lines: A list of strings, representing the items in the "Holidays and observances" list as plain text (with
        a leading "*" or "**" indicating the list level.
    :param sep: A string to use as the separator between different parts of a multi-level list.
    :return: A list of appropriately formatted holidays/observances.
    """
    formatted_list = []
    stack = []
    for line in lines:

        #print(f'line: {line}')

        # Get list level
        level = 0
        for c in line:
            if c == '*':
                level += 1
            else:
                break

        #print(f'level: {level}')

        line = line.strip().lstrip('*').rstrip(':')

        if level == 0:
            if not level:
                # Empty line
                break
            elif line.startswith('=='):
                # Beginning of new section
                break
            else:
                raise ParsingError(f'Unexpected line: {line}')

        elif level > len(stack) + 1:
            # We have encountered a "jump" in list levels, eg, a level-3 list immediately after a level-1 list.
            continue
            #raise ParsingError(f'Encountered level {level} item immediately after level {len(stack)} list: {line}')

        elif level > len(stack):
            # We've entered into a new sub-list.
            stack.append(line)

        elif level == len(stack):
            # This item is at the same level as the previous item. Replace the last item on the stack with this line.
            formatted_list.append(('', sep.join(stack).strip()))
            stack[-1] = line

        elif level < len(stack):
            # This item is at a lower level than the previous line.
            formatted_list.append(('', sep.join(stack).strip()))
            stack = stack[:level]
            stack[-1] = line

        else:
            raise ParsingError(f'Unexpected line: {line}')

    if stack:
        formatted_list.append(('', sep.join(stack)))

    return formatted_list


def parse_text(text: str) -> dict[str, list[tuple[str, str]]]:
    """
    Parse events from plain text.

    :param text: A string returned by the `plain_text` method of a :class:`wikitextparser.WikiText` object.
    :return: A dict containing the events.
    """
    lines = text.splitlines()
    events = empty_events_dict()
    h1 = None
    h2 = None
    for i, line in enumerate(lines):
        if match := re.match(H1_RE, line):
            h1 = match.group(1).strip()
            h2 = None

            if h1 not in events:
                # Exit if we find any other headings
                break

            if h1 == 'Holidays and observances':
                events[h1] = parse_holidays(lines[i + 1:])

        elif re.match(H2_RE, line):
            continue

        elif match := re.match(EVENT_RE, line):
            if not h1:
                raise ParsingError(f'Found event but missing heading: {match.string}')
            year = match.group(1)
            desc = match.group(2)
            events[h1].append((year, desc))
    return events


def parse_page(title: str, wiki: MediaWiki,
               last_rev_id: str) -> tuple[int, dict[str, list[tuple[str, str]]]]:
    page = wiki.page(title, auto_suggest=False)
    rev_id = page.revision_id
    if rev_id == last_rev_id:
        raise AlreadyScraped(f'Revision {rev_id} of page {title} already in DB.')
    parsed = wikitextparser.parse(page.wikitext)
    return rev_id, parse_text(parsed.plain_text())


def parse_date_to_db(month: str, date: int, db: DAO) -> int:
    """
    Fetch all events for a particular date from Wikipedia and store them in the database.

    :param month: The relevant month.
    :param date: The relevant date (day of month).
    :param db: The :class:`DAO` object in which to store the results.
    :return: The number of events saved to the DB.
    :raises AlreadyScraped: The current revision of the relevant Wikipedia page is already stored in the database.
    :raises ParsingError: There was an error in parsing the Wikipedia page.
    """
    wiki = MediaWiki(user_agent='onthisday (onthisday@devnool.net)')
    title = f'{month}_{date}'
    last_rev_id = db.get_revision(month, date)
    try:
        rev_id, parsed = parse_page(title, wiki, last_rev_id)
    except AlreadyScraped as e:
        logger.info(e.args[0])
        raise e
    except ParsingError as e:
        logger.error(f'Error when parsing {title}: {e.args[0]}')
        raise e
    if parsed == empty_events_dict():
        msg = f'Got empty dict when parsing {title}.'
        logger.error(msg)
        raise ParsingError(msg)
    n = db.insert_events(month, date, rev_id, parsed)
    db.insert_revision(month, date, rev_id)
    db.commit()
    logger.info(f'Inserted {n} events for {title}; revision ID {rev_id}.')
    return n


def parse_all_to_db(db: DAO):
    for m, d in iter_dates():
        try:
            parse_date_to_db(m, d, db)
        except AlreadyScraped:
            continue
