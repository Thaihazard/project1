from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import APIModel


class EmployeeOut(APIModel):
    id: str
    full_name: str
    email: str | None = None
    title: str
    department: str
    level: str
    role: str
    is_active: bool = True
    base_salary: int
    kpi_score: float
    soft_skill_score: float | None = None
    years_experience: float | None = None
    certification_count: int | None = None


class EmployeeEmailUpdate(APIModel):
    email: str


class EmployeeSalaryUpdate(APIModel):
    base_salary: int = Field(ge=0, le=1_000_000_000)


class EmployeeCreate(APIModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=3, max_length=255)
    title: str = Field(min_length=2, max_length=160)
    department: str = Field(min_length=2, max_length=120)
    level: str = Field(default="Mid", min_length=1, max_length=40)
    role: Literal["employee", "manager"] = "employee"
    base_salary: int = Field(ge=0, le=1_000_000_000)
    kpi_score: float = Field(default=80, ge=0, le=150)
    soft_skill_score: float = Field(default=4, ge=0, le=5)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    certification_count: int | None = Field(default=None, ge=0, le=100)
    initial_password: str | None = Field(default=None, min_length=12, max_length=128)

    @field_validator("initial_password", mode="before")
    @classmethod
    def validate_initial_password(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value

    @field_validator("full_name", "email", "title", "department", "level")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if email.count("@") != 1 or any(char.isspace() for char in email):
            raise ValueError("A valid email address is required")
        local, domain = email.split("@")
        if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("A valid email address is required")
        return email


class EmployeeImportResult(APIModel):
    created_count: int
    employees: list[EmployeeOut]


class EmployeeAssessmentCreate(APIModel):
    kpi_score: float | None = Field(default=None, ge=0, le=150)
    soft_skill_score: float | None = Field(default=None, ge=0, le=5)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    certification_count: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=2000)
