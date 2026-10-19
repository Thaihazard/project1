from datetime import date

from pydantic import Field, model_validator

from app.schemas.common import APIModel


class ContractCreate(APIModel):
    employee_id: str
    contract_type: str = Field(min_length=2, max_length=40)
    start_date: date
    end_date: date | None = None
    base_salary: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("endDate must be on or after startDate")
        return self


class ContractOut(APIModel):
    id: str
    employee_id: str
    employee_name: str
    contract_type: str
    start_date: date
    end_date: date | None = None
    base_salary: int
    status: str
