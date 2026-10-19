from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord


async def list_employee_attendance(db: AsyncSession, employee_id: str) -> list[AttendanceRecord]:
    rows = await db.scalars(select(AttendanceRecord).where(AttendanceRecord.employee_id == employee_id).order_by(AttendanceRecord.attendance_date.desc()))
    return list(rows)
