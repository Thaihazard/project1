from datetime import date

from pydantic import Field, model_validator

from app.schemas.common import APIModel


class LeaveCreate(APIModel):
    leave_type: str = Field(min_length=2, max_length=40)
    start_date: date
    end_date: date
    reason: str = Field(min_length=4, max_length=2000)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("endDate must be on or after startDate")
        return self


class LeaveDecision(APIModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class LeaveOut(APIModel):
    id: str
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    leave_days: int
