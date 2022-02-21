from typing import Union, Any

import pytz
from flask import Flask, make_response, request
from onthisday.calendar import make_calendar
from onthisday.common_data import date_from_yyyymmdd, int_or_none
from onthisday.db import InMemory, DAO

app = Flask(__name__)


class BadArgumentError(Exception): pass


def convert_args(args: dict[str, str]) -> dict[str, Any]:
    """
    Validate and convert request arguments (eg, GET parameters) to their appropriate form. Catches various errors for
    bad input, logs them and raises in their place a :class:`BadArgumentError` with a message that can be displayed to
    the user.

    :param args: The request arguments (eg, `request.args`).
    :return: A dict mapping arg names to appropriate values for use in :func:`make_calendar`.
    :raise BadArgumentError: If an error is encountered when converting the arguments.
    """
    converted: dict[str, Any] = {}

    try:
        converted['categories'] = {
            'Births': int_or_none(args.get('births')),
            'Deaths': int_or_none(args.get('deaths')),
            'Events': int_or_none(args.get('events')),
            'Holidays and observances': int_or_none(args.get('holidays'))
        }
    except ValueError as e:
        app.logger.exception(e)
        raise BadArgumentError('The number of events of each category to include in the calendar must be given as an '
                               'integer.')

    for k in converted['categories']:
        v = converted['categories'][k]
        if (v is not None) and (v < 0):
            app.logger.error(f'Value for "{k}" is less than zero ({v}).')
            raise BadArgumentError('The number of events of each category to include in the calendar must be greater '
                                   'than zero.')

    tz_str = args.get('timezone', 'UTC').replace(':', '/')
    try:
        converted['tz'] = pytz.timezone(tz_str)
    except pytz.UnknownTimeZoneError:
        raise BadArgumentError(f'Bad timezone: {tz_str}')

    try:
        converted['start'] = date_from_yyyymmdd(args.get('start'), '%Y-%m-%d')
        converted['end'] = date_from_yyyymmdd(args.get('end'), '%Y-%m-%d')
    except ValueError as e:
        app.logger.exception(e)
        raise BadArgumentError('The start and end dates for the calendar must be in the format "YYYY-MM-DD".')

    try:
        h_str, m_str = args.get('time', '9:0').split(':')
        hour = int(h_str)
        minute = int(m_str)
    except (TypeError, ValueError) as e:
        app.logger.exception(e)
        raise BadArgumentError('The time at which to schedule each event must be in the format "HH:MM".')

    if (hour < 0) or (hour > 23):
        raise BadArgumentError('The hour of the event must be between 0 and 23 (inclusive).')
    if (minute < 0) or (minute > 59):
        raise BadArgumentError('The minute (past the hour) of the event must be between 0 and 59 (inclusive).')

    converted['hour'] = hour
    converted['minute'] = minute

    return converted


@app.route('/calendar')
def calendar():
    try:
        args = convert_args(request.args)
    except BadArgumentError as e:
        return f'Error parsing input: {e.args[0]}'

    try:
        cal_str = make_calendar(app.config['db'], **args).to_ical().decode()
    except Exception as e:
        app.logger.exception(e)
        return ('Error generating calendar. Please check your input. If your input is correct, there may be an issue '
                'on the server side.')

    resp = make_response(cal_str)
    resp.headers['Content-Type'] = 'text/calendar'
    resp.headers['Content-Disposition'] = 'attachment; filename="onthisday.ics"'
    return resp


def run(db: Union[DAO, InMemory], host: str, port: int):
    app.config['db'] = db
    app.run(host, port)


if __name__ == '__main__':
    app.config['db'] = InMemory(DAO())
    app.run('localhost', 8080)
