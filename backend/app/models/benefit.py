from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BenefitOffering(Base):
    __tablename__ = "benefit_offerings"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    benefit_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    employer_contribution: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    employee_contribution: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BenefitEnrollment(Base):
    __tablename__ = "benefit_enrollments"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    benefit_id: Mapped[str] = mapped_column(ForeignKey("benefit_offerings.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    enrolled_on: Mapped[date] = mapped_column(Date, nullable=False)
