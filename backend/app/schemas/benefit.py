from pydantic import Field

from app.schemas.common import APIModel


class BenefitCreate(APIModel):
    name: str = Field(min_length=2, max_length=120)
    benefit_type: str = Field(min_length=2, max_length=40)
    description: str = Field(default="", max_length=2000)
    employer_contribution: int = Field(default=0, ge=0)
    employee_contribution: int = Field(default=0, ge=0)


class BenefitOut(APIModel):
    id: str
    name: str
    benefit_type: str
    description: str
    employer_contribution: int
    employee_contribution: int
    is_active: bool
    enrolled: bool = False


class BenefitEnrollmentOut(APIModel):
    id: str
    benefit_id: str
    benefit_name: str
    employee_id: str | None = None
    employee_name: str | None = None
    status: str
    enrolled_on: str


class BenefitDecision(APIModel):
    decision: str = Field(pattern="^(active|rejected)$")
