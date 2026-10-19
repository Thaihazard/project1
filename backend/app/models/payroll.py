from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PayPeriod(Base):
    __tablename__ = "pay_periods"
    __table_args__ = (CheckConstraint("start_date <= end_date", name="ck_pay_period_dates"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")


class PaySlip(Base):
    __tablename__ = "pay_slips"
    __table_args__ = (UniqueConstraint("employee_id", "pay_period_id", name="uq_pay_slip_employee_period"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    pay_period_id: Mapped[str] = mapped_column(ForeignKey("pay_periods.id"), index=True)
    base_salary: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    allowances: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    bonus: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    overtime_pay: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    gross_salary: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tax_deduction: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    insurance_deduction: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    other_deductions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tax_breakdown: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    net_salary: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
