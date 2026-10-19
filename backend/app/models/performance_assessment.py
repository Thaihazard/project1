from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmployeePerformanceAssessment(Base):
    __tablename__ = "employee_performance_assessments"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    assessed_on: Mapped[date] = mapped_column(Date, nullable=False)
    kpi_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    soft_skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    certification_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
