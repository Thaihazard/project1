from datetime import date, time, datetime

from pydantic import Field, model_validator

from app.schemas.common import APIModel


class OvertimeCreate(APIModel):
    work_date: date
    start_time: time
    end_time: time
    reason: str = Field(min_length=4, max_length=2000)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("endTime must be later than startTime on the same day")
        return self


class OvertimeDecision(APIModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class OvertimeOut(APIModel):
    id: str
    employee_id: str
    employee_name: str
    work_date: date
    start_time: time
    end_time: time
    hours: float
    reason: str
    status: str
    reviewer_id: str | None = None
    decided_at: datetime | None = None
