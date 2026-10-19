from pydantic import Field

from app.schemas.common import APIModel


class AIPredictInput(APIModel):
    current_salary: int = Field(gt=0, le=1_000_000_000)
    kpi_score: float = Field(default=80, ge=0, le=150)
    soft_skill_score: float = Field(default=4, ge=0, le=5)
    years_experience: float = Field(default=5, ge=0, le=60)
    certification_count: int = Field(default=0, ge=0, le=50)


class FeatureContribution(APIModel):
    feature: str
    impact: float
    explanation: str


class AIPredictOutput(APIModel):
    min_salary: int
    median_salary: int
    max_salary: int
    change_percent: float
    model_version: str
    explanation_method: str
    contributions: list[FeatureContribution]
    disclaimer: str


class BudgetSimulationInput(APIModel):
    kpi_weight: float = Field(ge=0, le=100)
    tenure_weight: float = Field(ge=0, le=100)
    current_budget: int = Field(gt=0)
