from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


async def list_employees(db: AsyncSession, manager_id: str | None = None) -> list[Employee]:
    statement = select(Employee).order_by(Employee.full_name)
    if manager_id:
        statement = statement.where(Employee.manager_id == manager_id, Employee.is_active.is_(True))
    result = await db.scalars(statement)
    return list(result)


async def get_employee(db: AsyncSession, employee_id: str) -> Employee | None:
    return await db.get(Employee, employee_id)
