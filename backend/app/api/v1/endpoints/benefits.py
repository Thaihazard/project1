from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.benefit import BenefitEnrollment, BenefitOffering
from app.models.employee import Employee
from app.models.user import User
from app.schemas.benefit import BenefitCreate, BenefitDecision, BenefitEnrollmentOut, BenefitOut

router = APIRouter(prefix="/benefits", tags=["benefits"])


@router.get("", response_model=list[BenefitOut])
async def list_benefits(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[BenefitOut]:
    rows = await db.scalars(select(BenefitOffering).where(BenefitOffering.is_active.is_(True)).order_by(BenefitOffering.name))
    enrollment_ids: set[str] = set()
    if user.employee_id:
        enrollment_ids = set((await db.scalars(select(BenefitEnrollment.benefit_id).where(
            BenefitEnrollment.employee_id == user.employee_id,
            BenefitEnrollment.status.in_(["pending", "active"]),
        ))).all())
    return [BenefitOut(id=item.id, name=item.name, benefit_type=item.benefit_type, description=item.description,
        employer_contribution=item.employer_contribution, employee_contribution=item.employee_contribution,
        is_active=item.is_active, enrolled=item.id in enrollment_ids) for item in rows]


@router.get("/me", response_model=list[BenefitEnrollmentOut])
async def my_benefits(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[BenefitEnrollmentOut]:
    if not user.employee_id:
        return []
    rows = await db.execute(select(BenefitEnrollment, BenefitOffering, Employee).join(BenefitOffering).join(
        Employee, Employee.id == BenefitEnrollment.employee_id
    ).where(
        BenefitEnrollment.employee_id == user.employee_id
    ).order_by(BenefitEnrollment.enrolled_on.desc()))
    return [BenefitEnrollmentOut(id=enrollment.id, benefit_id=offering.id, benefit_name=offering.name,
        employee_id=employee.id, employee_name=employee.full_name,
        status=enrollment.status, enrolled_on=enrollment.enrolled_on.isoformat()) for enrollment, offering, employee in rows]


@router.post("/{benefit_id}/enroll", response_model=BenefitEnrollmentOut, status_code=status.HTTP_201_CREATED)
async def enroll_benefit(benefit_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> BenefitEnrollmentOut:
    if user.role != "employee" or not user.employee_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only employees can enroll in benefits")
    benefit = await db.get(BenefitOffering, benefit_id)
    if benefit is None or not benefit.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benefit offering not found")
    existing = await db.scalar(select(BenefitEnrollment).where(
        BenefitEnrollment.employee_id == user.employee_id,
        BenefitEnrollment.benefit_id == benefit.id,
        BenefitEnrollment.status.in_(["pending", "active"]),
    ))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already enrolled in this benefit")
    item = BenefitEnrollment(id=str(uuid4()), employee_id=user.employee_id, benefit_id=benefit.id,
        status="pending", enrolled_on=date.today())
    db.add(item)
    await db.commit()
    employee = await db.get(Employee, user.employee_id)
    return BenefitEnrollmentOut(id=item.id, benefit_id=benefit.id, benefit_name=benefit.name,
        employee_id=employee.id, employee_name=employee.full_name,
        status=item.status, enrolled_on=item.enrolled_on.isoformat())


@router.post("", response_model=BenefitOut, status_code=status.HTTP_201_CREATED)
async def create_benefit(payload: BenefitCreate, db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr"))) -> BenefitOut:
    item = BenefitOffering(id=str(uuid4()), **payload.model_dump(), is_active=True)
    db.add(item)
    await db.commit()
    return BenefitOut(**payload.model_dump(), id=item.id, is_active=True)


@router.get("/enrollments", response_model=list[BenefitEnrollmentOut])
async def all_enrollments(db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("hr"))) -> list[BenefitEnrollmentOut]:
    rows = await db.execute(select(BenefitEnrollment, BenefitOffering, Employee)
        .join(BenefitOffering).join(Employee, Employee.id == BenefitEnrollment.employee_id)
        .order_by(BenefitEnrollment.enrolled_on.desc()))
    return [BenefitEnrollmentOut(id=enrollment.id, benefit_id=offering.id, benefit_name=offering.name,
        employee_id=employee.id, employee_name=employee.full_name,
        status=enrollment.status, enrolled_on=enrollment.enrolled_on.isoformat()) for enrollment, offering, employee in rows]


@router.patch("/enrollments/{enrollment_id}/decision", response_model=BenefitEnrollmentOut)
async def decide_enrollment(enrollment_id: str, payload: BenefitDecision, db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr"))) -> BenefitEnrollmentOut:
    enrollment = await db.get(BenefitEnrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benefit enrollment not found")
    if enrollment.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Enrollment has already been reviewed")
    enrollment.status = payload.decision
    offering = await db.get(BenefitOffering, enrollment.benefit_id)
    await db.commit()
    return BenefitEnrollmentOut(id=enrollment.id, benefit_id=offering.id, benefit_name=offering.name,
        employee_id=enrollment.employee_id, employee_name=(await db.get(Employee, enrollment.employee_id)).full_name,
        status=enrollment.status, enrolled_on=enrollment.enrolled_on.isoformat())
