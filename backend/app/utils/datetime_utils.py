from datetime import date, timedelta


def count_weekdays(start: date, end: date) -> int:
    if end < start:
        raise ValueError("end date must be on or after start date")
    return sum(1 for offset in range((end - start).days + 1) if (start + timedelta(days=offset)).weekday() < 5)
