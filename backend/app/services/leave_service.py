from datetime import date

from app.utils.datetime_utils import count_weekdays


def validate_leave_period(start: date, end: date) -> int:
    return count_weekdays(start, end)
