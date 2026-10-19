from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import LeaveCreate, LeaveDecision, LeaveOut
from app.services.leave_service import validate_leave_period

router = APIRouter(prefix="/leave", tags=["leave"])


def leave_out(item: LeaveRequest) -> LeaveOut:
    return LeaveOut(id=item.id, employee_id=item.employee_id, leave_type=item.leave_type, start_date=item.start_date,
                    end_date=item.end_date, reason=item.reason, status=item.status,
                    leave_days=validate_leave_period(item.start_date, item.end_date))


@router.get("/me", response_model=list[LeaveOut])
async def my_leave_requests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[LeaveOut]:
    if not user.employee_id:
        return []
    rows = await db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id == user.employee_id).order_by(LeaveRequest.start_date.desc()))
    return [leave_out(item) for item in rows]


@router.post("/requests", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
async def create_leave_request(payload: LeaveCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> LeaveOut:
    if user.role != "employee" or not user.employee_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only employees can submit leave requests")
    item = LeaveRequest(id=str(uuid4()), employee_id=user.employee_id, leave_type=payload.leave_type,
                        start_date=payload.start_date, end_date=payload.end_date, reason=payload.reason, status="pending")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return leave_out(item)


@router.get("/requests", response_model=list[LeaveOut])
async def team_leave_requests(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> list[LeaveOut]:
    statement = select(LeaveRequest).order_by(LeaveRequest.start_date.desc())
    if user.role == "manager":
        statement = statement.join(Employee, Employee.id == LeaveRequest.employee_id).where(Employee.manager_id == user.employee_id)
    rows = await db.scalars(statement)
    return [leave_out(item) for item in rows]


@router.patch("/requests/{request_id}/decision", response_model=LeaveOut)
async def decide_leave(request_id: str, payload: LeaveDecision, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> LeaveOut:
    item = await db.get(LeaveRequest, request_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave request not found")
    employee = await db.get(Employee, item.employee_id)
    if user.role == "manager" and (employee is None or employee.manager_id != user.employee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only review requests from your team")
    if item.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Leave request has already been reviewed")
    item.status = payload.decision
    item.reviewer_id = user.id
    await db.commit()
    await db.refresh(item)
    return leave_out(item)
