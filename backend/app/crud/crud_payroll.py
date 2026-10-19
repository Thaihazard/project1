from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.payroll import PayPeriod, PaySlip


async def list_pay_slips(db: AsyncSession, pay_period_id: str | None = None, manager_id: str | None = None) -> list[tuple[PaySlip, Employee, PayPeriod]]:
    statement = select(PaySlip, Employee, PayPeriod).join(Employee).join(PayPeriod)
    if pay_period_id:
        statement = statement.where(PaySlip.pay_period_id == pay_period_id)
    if manager_id:
        statement = statement.where(Employee.manager_id == manager_id)
    statement = statement.order_by(Employee.full_name)
    return list((await db.execute(statement)).all())


async def get_pay_slip(db: AsyncSession, pay_slip_id: str) -> tuple[PaySlip, Employee, PayPeriod] | None:
    statement = select(PaySlip, Employee, PayPeriod).join(Employee).join(PayPeriod).where(PaySlip.id == pay_slip_id)
    return (await db.execute(statement)).first()


async def get_employee_latest_slip(db: AsyncSession, employee_id: str) -> tuple[PaySlip, Employee, PayPeriod] | None:
    statement = (
        select(PaySlip, Employee, PayPeriod)
        .join(Employee)
        .join(PayPeriod)
        .where(PaySlip.employee_id == employee_id)
        .order_by(PayPeriod.end_date.desc())
    )
    return (await db.execute(statement)).first()
