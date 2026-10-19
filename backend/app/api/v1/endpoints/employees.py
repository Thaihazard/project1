import csv
import io
import secrets
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app.api.deps import require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.crud.crud_employee import list_employees
from app.models.employee import Employee
from app.models.compensation_history import EmployeeCompensationHistory
from app.models.performance_assessment import EmployeePerformanceAssessment
from app.models.payroll import PayPeriod, PaySlip
from app.models.user import User
from app.schemas.employee import EmployeeAssessmentCreate, EmployeeCreate, EmployeeEmailUpdate, EmployeeImportResult, EmployeeOut, EmployeeSalaryUpdate
from app.services.payroll_calculator import recalculate_slip

router = APIRouter(prefix="/employees", tags=["employees"])
MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 500
REQUIRED_IMPORT_COLUMNS = {"full_name", "email", "title", "department", "base_salary"}


def make_employee_and_user(payload: EmployeeCreate) -> tuple[Employee, User]:
    employee_id = f"EMP-{uuid4().hex[:12].upper()}"
    employee = Employee(
        id=employee_id,
        full_name=payload.full_name,
        email=payload.email,
        title=payload.title,
        department=payload.department,
        level=payload.level,
        role=payload.role,
        base_salary=payload.base_salary,
        kpi_score=payload.kpi_score,
        soft_skill_score=payload.soft_skill_score,
        years_experience=payload.years_experience,
        certification_count=payload.certification_count,
    )
    # If HR leaves this blank, the random password is unusable and the employee signs in with Google.
    user = User(
        id=f"USR-{uuid4().hex[:12].upper()}",
        username=employee_id,
        email=payload.email,
        password_hash=hash_password(payload.initial_password or secrets.token_urlsafe(48)),
        role=payload.role,
        employee_id=employee_id,
    )
    return employee, user


async def ensure_emails_available(db: AsyncSession, emails: list[str]) -> None:
    employee_email = await db.scalar(
        select(Employee.email).where(func.lower(Employee.email).in_(emails)).limit(1)
    )
    user_email = await db.scalar(
        select(User.email).where(func.lower(User.email).in_(emails)).limit(1)
    )
    if employee_email or user_email:
        raise HTTPException(status.HTTP_409_CONFLICT, "One or more email addresses are already linked to an account")


@router.get("", response_model=list[EmployeeOut])
async def employees(db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("manager", "hr"))) -> list[EmployeeOut]:
    return await list_employees(db, _.employee_id if _.role == "manager" else None)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("hr")),
) -> EmployeeOut:
    await ensure_emails_available(db, [payload.email])
    employee, account = make_employee_and_user(payload)
    db.add_all([employee, account, EmployeeCompensationHistory(
        id=f"CH-{uuid4().hex[:20].upper()}", employee_id=employee.id,
        base_salary=employee.base_salary, effective_from=date.today(),
        change_reason="Initial salary on employee creation", changed_by=user.id,
    )])
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email or employee ID already exists") from exc
    await db.refresh(employee)
    return employee


@router.post("/import", response_model=EmployeeImportResult, status_code=status.HTTP_201_CREATED)
async def import_employees(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("hr")),
) -> EmployeeImportResult:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a UTF-8 CSV file")
    raw = await file.read(MAX_IMPORT_BYTES + 1)
    if len(raw) > MAX_IMPORT_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "CSV file must be 5 MB or smaller")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CSV must use UTF-8 encoding") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    original_headers = reader.fieldnames or []
    header_map = {header.strip().lower(): header for header in original_headers if header}
    missing = REQUIRED_IMPORT_COLUMNS - header_map.keys()
    if missing:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing CSV columns: {', '.join(sorted(missing))}")

    parsed: list[tuple[int, EmployeeCreate]] = []
    errors: list[str] = []
    row_count = 0
    for line_number, raw_row in enumerate(reader, start=2):
        if not raw_row or not any((value or "").strip() for value in raw_row.values()):
            continue
        row_count += 1
        if row_count > MAX_IMPORT_ROWS:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"CSV may contain at most {MAX_IMPORT_ROWS} employees")
        values = {key: raw_row.get(header, "") for key, header in header_map.items()}
        for optional_feature in ("years_experience", "certification_count"):
            if optional_feature in values and not (values[optional_feature] or "").strip():
                values[optional_feature] = None
        for key, default in (("level", "Mid"), ("role", "employee"), ("kpi_score", "80"), ("soft_skill_score", "4")):
            if not values.get(key, "").strip():
                values[key] = default
        try:
            parsed.append((line_number, EmployeeCreate.model_validate(values)))
        except ValidationError as exc:
            errors.append(f"Row {line_number}: invalid employee data ({exc})")

    if not parsed and not errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CSV contains no employee rows")
    seen: set[str] = set()
    for line_number, employee in parsed:
        if employee.email in seen:
            errors.append(f"Row {line_number}: duplicate email in file")
        seen.add(employee.email)
    if errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"message": "CSV validation failed", "errors": errors[:30]})

    await ensure_emails_available(db, [employee.email for _, employee in parsed])
    records = [make_employee_and_user(employee) for _, employee in parsed]
    db.add_all([record for pair in records for record in pair])
    db.add_all([EmployeeCompensationHistory(
        id=f"CH-{uuid4().hex[:20].upper()}", employee_id=employee.id,
        base_salary=employee.base_salary, effective_from=date.today(),
        change_reason="Initial salary from employee CSV import", changed_by=user.id,
    ) for employee, _account in records])
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Some email addresses or generated employee IDs already exist; no rows were imported") from exc
    for employee, _user in records:
        await db.refresh(employee)
    return EmployeeImportResult(created_count=len(records), employees=[employee for employee, _user in records])


@router.patch("/{employee_id}/email", response_model=EmployeeOut)
async def update_employee_email(
    employee_id: str,
    payload: EmployeeEmailUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr")),
) -> EmployeeOut:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    email = payload.email.strip().lower()
    if len(email) > 255 or email.count("@") != 1 or any(char.isspace() for char in email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A valid email address is required")
    duplicate = await db.scalar(select(Employee.id).where(func.lower(Employee.email) == email, Employee.id != employee_id))
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already assigned to another employee")
    employee.email = email
    await db.commit()
    await db.refresh(employee)
    return employee


@router.patch("/{employee_id}/salary", response_model=EmployeeOut)
async def update_employee_salary(
    employee_id: str,
    payload: EmployeeSalaryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("hr")),
) -> EmployeeOut:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    if payload.base_salary != employee.base_salary:
        effective_date = date.today()
        latest_history = await db.scalar(
            select(EmployeeCompensationHistory)
            .where(EmployeeCompensationHistory.employee_id == employee.id,
                   EmployeeCompensationHistory.effective_to.is_(None))
            .order_by(EmployeeCompensationHistory.effective_from.desc())
            .limit(1)
        )
        if latest_history:
            latest_history.effective_to = effective_date
        db.add(EmployeeCompensationHistory(
            id=f"CH-{uuid4().hex[:20].upper()}", employee_id=employee.id,
            base_salary=payload.base_salary, effective_from=effective_date,
            change_reason="Salary updated by HR", changed_by=user.id,
        ))
    employee.base_salary = payload.base_salary
    draft_rows = await db.execute(
        select(PaySlip, PayPeriod)
        .join(PayPeriod, PayPeriod.id == PaySlip.pay_period_id)
        .where(PaySlip.employee_id == employee.id, PaySlip.status == "draft")
    )
    for slip, period in draft_rows:
        if period.status != "approved":
            slip.base_salary = employee.base_salary
            recalculate_slip(slip)
    await db.commit()
    await db.refresh(employee)
    return employee


@router.post("/{employee_id}/assessments", status_code=status.HTTP_201_CREATED)
async def record_employee_assessment(
    employee_id: str,
    payload: EmployeeAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("hr")),
) -> dict[str, str | int | float | None]:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    values = payload.model_dump(exclude={"notes"})
    if not any(value is not None for value in values.values()):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide at least one assessment value")
    for field, value in values.items():
        if value is not None:
            setattr(employee, field, value)
    assessment = EmployeePerformanceAssessment(
        id=f"PA-{uuid4().hex[:20].upper()}", employee_id=employee.id,
        assessed_on=date.today(), kpi_score=employee.kpi_score,
        soft_skill_score=employee.soft_skill_score,
        years_experience=employee.years_experience,
        certification_count=employee.certification_count,
        notes=payload.notes, assessed_by=user.id,
    )
    db.add(assessment)
    await db.commit()
    return {
        "id": assessment.id,
        "employee_id": employee.id,
        "assessed_on": assessment.assessed_on.isoformat(),
        "kpi_score": assessment.kpi_score,
        "soft_skill_score": assessment.soft_skill_score,
        "years_experience": assessment.years_experience,
        "certification_count": assessment.certification_count,
    }


@router.delete("/{employee_id}", response_model=EmployeeOut)
async def deactivate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr")),
) -> EmployeeOut:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    if employee.is_active:
        employee.is_active = False
        account = await db.scalar(
            select(User).where(User.employee_id == employee.id, User.role != "disabled")
        )
        if account is not None:
            account.role = "disabled"
            account.username = f"former-{uuid4().hex}"
            account.email = None
            account.firebase_uid = None
            account.password_hash = hash_password(secrets.token_urlsafe(48))
        await db.commit()
        await db.refresh(employee)
    return employee


@router.post("/{employee_id}/restore", response_model=EmployeeOut)
async def restore_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr")),
) -> EmployeeOut:
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    if not employee.is_active:
        if employee.role not in {"employee", "manager"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "This employee role cannot be restored from this page")
        active_account = await db.scalar(
            select(User.id).where(User.employee_id == employee.id, User.role != "disabled")
        )
        if active_account:
            raise HTTPException(status.HTTP_409_CONFLICT, "An active account is already linked to this employee")
        email_account = await db.scalar(
            select(User.id).where(func.lower(User.email) == (employee.email or "").lower())
        ) if employee.email else None
        if email_account:
            raise HTTPException(status.HTTP_409_CONFLICT, "This email is linked to another account")
        employee.is_active = True
        db.add(User(
            id=f"USR-{uuid4().hex[:12].upper()}",
            username=employee.id,
            email=employee.email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            role=employee.role,
            employee_id=employee.id,
        ))
        await db.commit()
        await db.refresh(employee)
    return employee

