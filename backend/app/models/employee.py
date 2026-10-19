from sqlalchemy import BigInteger, Boolean, Float, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False, default="Mid")
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="employee")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    manager_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    base_salary: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    kpi_score: Mapped[float] = mapped_column(Float, nullable=False, default=80)
    soft_skill_score: Mapped[float] = mapped_column(Float, nullable=False, default=4)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    certification_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
