from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import Base, BenefitOffering, Contract, Employee, PayPeriod, PaySlip, PayrollProposal, User


async def initialize_database() -> None:
    if settings.app_env.lower() == "production" and settings.jwt_secret == "dev-only-change-this-secret-before-deployment":
        raise RuntimeError("Set JWT_SECRET to a unique secret before running in production")
    if settings.app_env.lower() != "production":
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if settings.app_env.lower() != "production":
            benefit_seeds = [
                BenefitOffering(id="BEN-HEALTH", name="Bảo hiểm sức khỏe bổ sung", benefit_type="insurance", description="Gói bảo hiểm sức khỏe theo chính sách công ty; mức đóng là minh họa, HR cần xác nhận.", employer_contribution=500_000, employee_contribution=0),
                BenefitOffering(id="BEN-MEAL", name="Hỗ trợ ăn ca", benefit_type="allowance", description="Chế độ hỗ trợ bữa ăn theo ngày làm việc.", employer_contribution=730_000, employee_contribution=0),
                BenefitOffering(id="BEN-LEARNING", name="Ngân sách học tập", benefit_type="development", description="Ngân sách đào tạo theo chính sách và phê duyệt của quản lý.", employer_contribution=2_000_000, employee_contribution=0),
            ]
            for offering in benefit_seeds:
                if not await db.get(BenefitOffering, offering.id):
                    db.add(offering)
            await db.flush()
        if await db.scalar(select(User.id).limit(1)):
            if settings.app_env.lower() != "production":
                await db.execute(update(Employee).where(Employee.id.in_(["EMP-1001", "EMP-1002"])).values(manager_id="EMP-1003"))
                contract_seeds = [
                    Contract(id="CON-EMP-1001", employee_id="EMP-1001", contract_type="Indefinite", start_date=date(2023, 1, 1), base_salary=25_000_000, status="active"),
                    Contract(id="CON-EMP-1002", employee_id="EMP-1002", contract_type="Fixed-term", start_date=date(2025, 1, 1), end_date=date(2027, 1, 1), base_salary=20_000_000, status="active"),
                    Contract(id="CON-EMP-1003", employee_id="EMP-1003", contract_type="Indefinite", start_date=date(2022, 6, 1), base_salary=27_000_000, status="active"),
                ]
                for contract in contract_seeds:
                    if await db.get(Employee, contract.employee_id) and not await db.get(Contract, contract.id):
                        db.add(contract)
                if not await db.get(PayrollProposal, "B-204"):
                    db.add_all([
                        PayrollProposal(id="B-204", employee_id="EMP-1001", pay_period_id="2026-Q3", proposed_change_percent=10.7, proposed_change_amount=3_000_000, reason="High performance; below internal market range."),
                        PayrollProposal(id="B-205", employee_id="EMP-1003", pay_period_id="2026-Q3", proposed_change_percent=4.2, proposed_change_amount=1_200_000, reason="Expanded scope of responsibilities."),
                        PayrollProposal(id="B-207", employee_id="EMP-1002", pay_period_id="2026-Q3", proposed_change_percent=6.0, proposed_change_amount=1_800_000, reason="Strong performance review results."),
                    ])
                await db.commit()
            return
        if settings.app_env.lower() == "production":
            return

        employees = [
            Employee(id="EMP-1001", full_name="Nguyen Van An", title="Senior Backend Engineer", department="Engineering", level="Senior", role="employee", manager_id="EMP-1003", base_salary=25_000_000, kpi_score=92, soft_skill_score=4.4),
            Employee(id="EMP-1002", full_name="Tran Thi Binh", title="Mid Frontend Engineer", department="Engineering", level="Mid", role="employee", manager_id="EMP-1003", base_salary=20_000_000, kpi_score=74, soft_skill_score=3.8),
            Employee(id="EMP-1003", full_name="Le Minh Khoa", title="Senior Data Engineer", department="Data Platform", level="Senior", role="manager", base_salary=27_000_000, kpi_score=89, soft_skill_score=4.5),
        ]
        period = PayPeriod(id="2026-Q3", name="Q3 2026", start_date=date(2026, 7, 1), end_date=date(2026, 9, 30), status="draft")
        db.add_all(employees)
        db.add(period)
        await db.flush()
        db.add_all([
            Contract(id="CON-EMP-1001", employee_id="EMP-1001", contract_type="Indefinite", start_date=date(2023, 1, 1), base_salary=25_000_000, status="active"),
            Contract(id="CON-EMP-1002", employee_id="EMP-1002", contract_type="Fixed-term", start_date=date(2025, 1, 1), end_date=date(2027, 1, 1), base_salary=20_000_000, status="active"),
            Contract(id="CON-EMP-1003", employee_id="EMP-1003", contract_type="Indefinite", start_date=date(2022, 6, 1), base_salary=27_000_000, status="active"),
        ])
        slips = [
            PaySlip(id="PS-2026Q3-1001", employee_id="EMP-1001", pay_period_id=period.id, base_salary=25_000_000, allowances=2_000_000, bonus=1_000_000, overtime_pay=500_000, gross_salary=28_500_000, tax_deduction=2_000_000, insurance_deduction=2_100_000, other_deductions=400_000, tax_breakdown=[{"name": "Personal income tax (demo)", "amount": 2_000_000}], net_salary=24_000_000, status="draft", issue_date=date(2026, 9, 30)),
            PaySlip(id="PS-2026Q3-1002", employee_id="EMP-1002", pay_period_id=period.id, base_salary=20_000_000, allowances=1_500_000, bonus=0, overtime_pay=300_000, gross_salary=21_800_000, tax_deduction=1_200_000, insurance_deduction=1_680_000, other_deductions=0, tax_breakdown=[{"name": "Personal income tax (demo)", "amount": 1_200_000}], net_salary=18_920_000, status="draft", issue_date=date(2026, 9, 30)),
            PaySlip(id="PS-2026Q3-1003", employee_id="EMP-1003", pay_period_id=period.id, base_salary=27_000_000, allowances=2_000_000, bonus=500_000, overtime_pay=0, gross_salary=29_500_000, tax_deduction=2_300_000, insurance_deduction=2_200_000, other_deductions=0, tax_breakdown=[{"name": "Personal income tax (demo)", "amount": 2_300_000}], net_salary=25_000_000, status="draft", issue_date=date(2026, 9, 30)),
        ]
        db.add_all(slips)
        db.add_all([
            PayrollProposal(id="B-204", employee_id="EMP-1001", pay_period_id=period.id, proposed_change_percent=10.7, proposed_change_amount=3_000_000, reason="High performance; below internal market range."),
            PayrollProposal(id="B-205", employee_id="EMP-1003", pay_period_id=period.id, proposed_change_percent=4.2, proposed_change_amount=1_200_000, reason="Expanded scope of responsibilities."),
            PayrollProposal(id="B-207", employee_id="EMP-1002", pay_period_id=period.id, proposed_change_percent=6.0, proposed_change_amount=1_800_000, reason="Strong performance review results."),
        ])
        db.add_all([
            User(id="USR-HR-001", username="hr", password_hash=hash_password(settings.demo_admin_password), role="hr"),
            User(id="USR-MGR-001", username="manager", password_hash=hash_password(settings.demo_manager_password), role="manager", employee_id="EMP-1003"),
            User(id="USR-EMP-001", username="employee", password_hash=hash_password(settings.demo_employee_password), role="employee", employee_id="EMP-1001"),
        ])
        await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="1.0.0", description="Versioned API gateway for AI CompHub.", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
@app.get(f"{settings.api_v1_prefix}/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
