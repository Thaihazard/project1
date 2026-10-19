from datetime import date, datetime, timezone

from pydantic import field_serializer

from app.schemas.common import APIModel


class AttendanceOut(APIModel):
    id: str
    employee_id: str
    employee_name: str | None = None
    attendance_date: date
    check_in: datetime
    check_out: datetime | None = None
    status: str

    @field_serializer("check_in", "check_out", when_used="unless-none")
    def serialize_timestamp_as_utc(self, value: datetime) -> datetime:
        # SQLite drops timezone metadata for DateTime columns; stored values are UTC.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
