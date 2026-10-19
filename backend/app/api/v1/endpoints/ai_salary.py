from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.ai_prediction import AIPrediction
from app.models.user import User
from app.schemas.ai import AIPredictInput, AIPredictOutput, BudgetSimulationInput
from app.services.ai_engine import salary_prediction_service

router = APIRouter(prefix="/ai-salary", tags=["ai-salary"])


@router.post("/predict", response_model=AIPredictOutput)
async def predict_salary(payload: AIPredictInput, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AIPredictOutput:
    return await _predict_and_record(payload, user, db)


@router.post("/simulate", response_model=AIPredictOutput)
async def simulate_salary(payload: AIPredictInput, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AIPredictOutput:
    return await _predict_and_record(payload, user, db)


async def _predict_and_record(payload: AIPredictInput, user: User, db: AsyncSession) -> AIPredictOutput:
    result = salary_prediction_service.predict(payload)
    db.add(AIPrediction(
        id=f"AIP-{uuid4().hex[:20].upper()}",
        employee_id=user.employee_id,
        created_by=user.id,
        input_features=payload.model_dump(mode="json"),
        predicted_min=result.min_salary,
        predicted_median=result.median_salary,
        predicted_max=result.max_salary,
        change_percent=result.change_percent,
        model_version=result.model_version,
        explanation_method=result.explanation_method,
        explanation_json=[item.model_dump(mode="json") for item in result.contributions],
    ))
    await db.commit()
    return result


@router.post("/budget-simulation")
async def simulate_budget(payload: BudgetSimulationInput, _: User = Depends(require_roles("hr"))) -> dict[str, float | str]:
    if payload.kpi_weight + payload.tenure_weight > 100:
        raise HTTPException(422, "KPI and tenure weights cannot exceed 100% combined")
    delta = (payload.kpi_weight - 40) * 0.0015 - (payload.tenure_weight - 25) * 0.0005
    projected = round(payload.current_budget * (1 + delta))
    return {"currentBudget": payload.current_budget, "projectedBudget": projected,
            "changeAmount": round(projected - payload.current_budget, 2), "modelVersion": "baseline-demo-v1",
            "disclaimer": "Illustrative simulation; it does not approve or apply compensation changes."}
