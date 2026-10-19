from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.employee import Employee
from app.models.overtime import OvertimeRequest
from app.models.user import User
from app.schemas.overtime import OvertimeCreate, OvertimeDecision, OvertimeOut

router = APIRouter(prefix="/overtime", tags=["overtime"])


def to_out(item: OvertimeRequest, employee: Employee) -> OvertimeOut:
    duration = (datetime.combine(item.work_date, item.end_time) - datetime.combine(item.work_date, item.start_time)).total_seconds() / 3600
    return OvertimeOut(id=item.id, employee_id=item.employee_id, employee_name=employee.full_name,
        work_date=item.work_date, start_time=item.start_time, end_time=item.end_time,
        hours=round(duration, 2), reason=item.reason, status=item.status,
        reviewer_id=item.reviewer_id, decided_at=item.decided_at)


@router.get("/me", response_model=list[OvertimeOut])
async def my_overtime(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[OvertimeOut]:
    if not user.employee_id:
        return []
    rows = await db.execute(select(OvertimeRequest, Employee).join(Employee).where(
        OvertimeRequest.employee_id == user.employee_id
    ).order_by(OvertimeRequest.work_date.desc()))
    return [to_out(item, employee) for item, employee in rows]


@router.post("/requests", response_model=OvertimeOut, status_code=status.HTTP_201_CREATED)
async def create_overtime(payload: OvertimeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> OvertimeOut:
    if user.role != "employee" or not user.employee_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only employees can submit overtime requests")
    item = OvertimeRequest(id=str(uuid4()), employee_id=user.employee_id, work_date=payload.work_date,
        start_time=payload.start_time, end_time=payload.end_time, reason=payload.reason, status="pending")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    employee = await db.get(Employee, user.employee_id)
    return to_out(item, employee)


@router.get("/requests", response_model=list[OvertimeOut])
async def team_overtime(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> list[OvertimeOut]:
    statement = select(OvertimeRequest, Employee).join(Employee)
    if user.role == "manager":
        statement = statement.where(Employee.manager_id == user.employee_id)
    rows = await db.execute(statement.order_by(OvertimeRequest.work_date.desc()))
    return [to_out(item, employee) for item, employee in rows]


@router.patch("/requests/{request_id}/decision", response_model=OvertimeOut)
async def decide_overtime(request_id: str, payload: OvertimeDecision,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> OvertimeOut:
    item = await db.get(OvertimeRequest, request_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Overtime request not found")
    employee = await db.get(Employee, item.employee_id)
    if user.role == "manager" and (employee is None or employee.manager_id != user.employee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only review requests from your team")
    if item.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Overtime request has already been reviewed")
    item.status = payload.decision
    item.reviewer_id = user.id
    item.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return to_out(item, employee)
