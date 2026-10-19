from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.crud.crud_payroll import get_employee_latest_slip, get_pay_slip, list_pay_slips
from app.models.employee import Employee
from app.models.payroll import PayPeriod, PaySlip
from app.models.payroll_proposal import PayrollProposal
from app.models.user import User
from app.schemas.payroll import CalculatePayrollRequest, MyCompensationOut, PaySlipOut, PayrollProposalDecision, PayrollProposalOut
from app.services.payroll_calculator import recalculate_slip
from app.utils.xlsx import build_xlsx

router = APIRouter(prefix="/payroll", tags=["payroll"])


def proposal_out(proposal: PayrollProposal, employee: Employee) -> PayrollProposalOut:
    return PayrollProposalOut(id=proposal.id, employee_id=employee.id, employee_name=employee.full_name,
        department=employee.department, pay_period_id=proposal.pay_period_id,
        proposed_change_percent=proposal.proposed_change_percent, proposed_change_amount=proposal.proposed_change_amount,
        current_salary=proposal.current_salary, proposed_salary=proposal.proposed_salary,
        prediction_id=proposal.prediction_id, reason=proposal.reason, status=proposal.status,
        decided_at=proposal.decided_at, decision_note=proposal.decision_note)


@router.get("/proposals", response_model=list[PayrollProposalOut])
async def payroll_proposals(db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("hr"))) -> list[PayrollProposalOut]:
    rows = await db.execute(select(PayrollProposal, Employee).join(Employee).order_by(PayrollProposal.id))
    return [proposal_out(proposal, employee) for proposal, employee in rows]


@router.post("/proposals/{proposal_id}/decision", response_model=PayrollProposalOut)
async def decide_payroll_proposal(
    proposal_id: str, payload: PayrollProposalDecision, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("hr")),
) -> PayrollProposalOut:
    proposal = await db.get(PayrollProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payroll proposal not found")
    if proposal.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposal has already been reviewed")
    proposal.status = payload.decision
    proposal.reviewer_id = user.id
    proposal.decided_at = datetime.now(timezone.utc)
    proposal.decision_note = payload.decision_note
    await db.commit()
    await db.refresh(proposal)
    employee = await db.get(Employee, proposal.employee_id)
    return proposal_out(proposal, employee)


def to_output(row: tuple[PaySlip, Employee, PayPeriod]) -> PaySlipOut:
    slip, employee, period = row
    return PaySlipOut(
        id=slip.id, employee_id=employee.id, employee_name=employee.full_name, department=employee.department,
        pay_period_id=period.id, pay_period_name=period.name, base_salary=slip.base_salary,
        allowances=slip.allowances, bonus=slip.bonus, overtime_pay=slip.overtime_pay,
        gross_salary=slip.gross_salary, tax_deduction=slip.tax_deduction,
        insurance_deduction=slip.insurance_deduction, other_deductions=slip.other_deductions,
        tax_breakdown=slip.tax_breakdown or [], net_salary=slip.net_salary,
        status=slip.status, issue_date=slip.issue_date,
    )


@router.get("/payslips", response_model=list[PaySlipOut])
async def payslips(
    pay_period_id: str | None = Query(default=None, alias="payPeriodId"), db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("manager", "hr")),
) -> list[PaySlipOut]:
    return [to_output(row) for row in await list_pay_slips(db, pay_period_id, user.employee_id if user.role == "manager" else None)]


@router.get("/me/payslips/latest", response_model=PaySlipOut)
async def my_latest_payslip(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("employee", "manager", "hr"))) -> PaySlipOut:
    if not user.employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No employee profile is linked to this account")
    row = await get_employee_latest_slip(db, user.employee_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No payslip found")
    return to_output(row)


@router.get("/me/compensation", response_model=MyCompensationOut)
async def my_compensation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("employee", "manager", "hr")),
) -> MyCompensationOut:
    if not user.employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No employee profile is linked to this account")
    employee = await db.get(Employee, user.employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee profile not found")
    latest = await get_employee_latest_slip(db, employee.id)
    return MyCompensationOut(
        employee_id=employee.id,
        employee_name=employee.full_name,
        department=employee.department,
        title=employee.title,
        base_salary=employee.base_salary,
        latest_payslip=to_output(latest) if latest else None,
    )


@router.get("/me/payslips/{pay_slip_id}", response_model=PaySlipOut)
async def my_payslip(pay_slip_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("employee", "manager", "hr"))) -> PaySlipOut:
    row = await get_pay_slip(db, pay_slip_id)
    if row is None or (user.role == "employee" and row[0].employee_id != user.employee_id) or (user.role == "manager" and row[1].manager_id != user.employee_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payslip not found")
    return to_output(row)


@router.post("/calculate", response_model=list[PaySlipOut])
async def calculate_payroll(payload: CalculatePayrollRequest, db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("hr"))) -> list[PaySlipOut]:
    pay_period_id = payload.pay_period_id
    period = await db.get(PayPeriod, pay_period_id)
    if period is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pay period not found")
    if period.status == "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "This payroll period is already approved and cannot be recalculated")
    rows = await list_pay_slips(db, pay_period_id)
    slips_by_employee = {slip.employee_id: slip for slip, _, _ in rows}
    employees = list(await db.scalars(
        select(Employee).where(Employee.is_active.is_(True)).order_by(Employee.full_name)
    ))
    for employee in employees:
        slip = slips_by_employee.get(employee.id)
        if slip is None:
            slip = PaySlip(
                id=f"PS-{uuid4().hex[:20].upper()}",
                employee_id=employee.id,
                pay_period_id=period.id,
                base_salary=employee.base_salary,
                status="draft",
            )
            db.add(slip)
        elif slip.status != "approved":
            # The employee profile is the source of truth for draft base salary.
            slip.base_salary = employee.base_salary
        if slip.status != "approved":
            recalculate_slip(slip)
            slip.status = "draft"
    await db.commit()
    return [to_output(row) for row in await list_pay_slips(db, pay_period_id)]


@router.post("/periods/{pay_period_id}/approve", response_model=list[PaySlipOut])
async def approve_payroll_period(
    pay_period_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_roles("hr")),
) -> list[PaySlipOut]:
    period = await db.get(PayPeriod, pay_period_id)
    if period is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pay period not found")
    rows = await list_pay_slips(db, pay_period_id)
    drafts = [slip for slip, _, _ in rows if slip.status == "draft"]
    if not drafts:
        raise HTTPException(status.HTTP_409_CONFLICT, "No draft payslips are available for approval")
    for slip in drafts:
        slip.status = "approved"
    period.status = "approved"
    await db.commit()
    return [to_output(row) for row in await list_pay_slips(db, pay_period_id)]


@router.get("/export")
async def export_payroll(
    pay_period_id: str = Query(alias="payPeriodId"), db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr")),
) -> Response:
    rows = await list_pay_slips(db, pay_period_id)
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No payslips found for this pay period")
    headers = ["Employee ID", "Employee", "Department", "Pay period", "Gross salary", "Tax", "Insurance", "Other deductions", "Net salary", "Status"]
    values = [[s.employee_id, e.full_name, e.department, p.name, s.gross_salary, s.tax_deduction,
               s.insurance_deduction, s.other_deductions, s.net_salary, s.status] for s, e, p in rows]
    file_bytes = build_xlsx(headers, values)
    return Response(content=file_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="payroll-{pay_period_id}.xlsx"'})
