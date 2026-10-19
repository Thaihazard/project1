from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    employee_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    input_features: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    predicted_min: Mapped[int] = mapped_column(BigInteger, nullable=False)
    predicted_median: Mapped[int] = mapped_column(BigInteger, nullable=False)
    predicted_max: Mapped[int] = mapped_column(BigInteger, nullable=False)
    change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    explanation_method: Mapped[str] = mapped_column(String(80), nullable=False)
    explanation_json: Mapped[list[dict]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
