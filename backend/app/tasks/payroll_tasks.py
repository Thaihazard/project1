import asyncio

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.payroll import PaySlip
from app.services.payroll_calculator import recalculate_slip


async def _recalculate_period(pay_period_id: str) -> int:
    async with SessionLocal() as db:
        slips = list(await db.scalars(select(PaySlip).where(PaySlip.pay_period_id == pay_period_id)))
        for slip in slips:
            recalculate_slip(slip)
            slip.status = "draft"
        await db.commit()
        return len(slips)


if celery_app is not None:
    @celery_app.task(name="payroll.calculate_period")
    def calculate_payroll_period(pay_period_id: str) -> dict[str, int | str]:
        count = asyncio.run(_recalculate_period(pay_period_id))
        return {"payPeriodId": pay_period_id, "processed": count}
else:
    def calculate_payroll_period(pay_period_id: str) -> dict[str, int | str]:
        raise RuntimeError("Install celery[redis] to run payroll background tasks")
