from datetime import date

from flask import Flask, make_response
from onthisday.calendar import make_calendar
from onthisday.db import InMemory, DAO

app = Flask(__name__)

db = InMemory(DAO())

@app.route('/calendar')
def calendar(birth: int = 1, death: int = 1, event: int = 1, holiday: int = 1,
             start_year: int = None, start_month: int = None, start_date: int = None,
             end_year: int = None, end_month: int = None, end_date: int = None,
             hour: int = 9, minute: int = 0):
    today = date.today()
    start = date(
        start_year if start_year is not None else today.year,
        start_month if start_month is not None else today.month,
        start_date if start_date is not None else today.day
    )
    end = date(
        end_year if end_year is not None else start.year + 1,
        end_month if end_month is not None else start.month,
        end_date if end_date is not None else start.day
    )
    categories = {
        'Births': birth,
        'Deaths': death,
        'Events': event,
        'Holidays and observances': holiday
    }
    resp = make_response(make_calendar(db, start, end, (hour, minute), categories).to_ical().decode())
    resp.headers['Content-Type'] = 'text/calendar'
    resp.headers['Content-Disposition'] = 'attachment; filename="onthisday.ics"'
    return resp

if __name__ == '__main__':
    app.run('localhost', 8080)
