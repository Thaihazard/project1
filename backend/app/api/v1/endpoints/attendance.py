from datetime import datetime, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.employee import Employee
from app.crud.crud_attendance import list_employee_attendance
from app.models.user import User
from app.schemas.attendance import AttendanceOut

router = APIRouter(prefix="/attendance", tags=["attendance"])
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@router.get("/me", response_model=list[AttendanceOut])
async def my_attendance(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[AttendanceOut]:
    if not user.employee_id:
        return []
    return await list_employee_attendance(db, user.employee_id)


@router.post("/check-in", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def check_in(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> AttendanceOut:
    if not user.employee_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "No employee profile is linked to this account")
    now = datetime.now(timezone.utc)
    today = now.astimezone(VIETNAM_TZ).date()
    existing = await db.scalar(select(AttendanceRecord).where(AttendanceRecord.employee_id == user.employee_id, AttendanceRecord.attendance_date == today))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Attendance has already been checked in today")
    record = AttendanceRecord(id=str(uuid4()), employee_id=user.employee_id, attendance_date=today, check_in=now, status="present")
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/check-out", response_model=AttendanceOut)
async def check_out(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> AttendanceOut:
    if not user.employee_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "No employee profile is linked to this account")
    now = datetime.now(timezone.utc)
    today = now.astimezone(VIETNAM_TZ).date()
    record = await db.scalar(select(AttendanceRecord).where(
        AttendanceRecord.employee_id == user.employee_id,
        AttendanceRecord.attendance_date == today,
    ))
    if record is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Check in before checking out")
    if record.check_out is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Attendance has already been checked out today")
    record.check_out = now
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/team", response_model=list[AttendanceOut])
async def team_attendance(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> list[AttendanceOut]:
    statement = select(AttendanceRecord, Employee).join(Employee, Employee.id == AttendanceRecord.employee_id)
    if user.role == "manager":
        statement = statement.where(Employee.manager_id == user.employee_id)
    rows = await db.execute(statement.order_by(AttendanceRecord.attendance_date.desc(), Employee.full_name))
    return [AttendanceOut(id=record.id, employee_id=employee.id, employee_name=employee.full_name,
        attendance_date=record.attendance_date, check_in=record.check_in, check_out=record.check_out,
        status=record.status) for record, employee in rows]
