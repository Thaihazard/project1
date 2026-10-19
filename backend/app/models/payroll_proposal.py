from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PayrollProposal(Base):
    __tablename__ = "payroll_proposals"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    pay_period_id: Mapped[str] = mapped_column(ForeignKey("pay_periods.id"), index=True)
    prediction_id: Mapped[str | None] = mapped_column(ForeignKey("ai_predictions.id"), nullable=True, index=True)
    current_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proposed_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proposed_change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_change_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
