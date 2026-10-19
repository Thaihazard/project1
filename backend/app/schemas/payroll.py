from datetime import date, datetime

from pydantic import Field

from app.schemas.common import APIModel


class TaxDeductionOut(APIModel):
    name: str
    amount: int


class PaySlipOut(APIModel):
    id: str
    employee_id: str
    employee_name: str
    department: str | None = None
    pay_period_id: str
    pay_period_name: str | None = None
    base_salary: int
    allowances: int
    bonus: int
    overtime_pay: int
    gross_salary: int
    tax_deduction: int
    insurance_deduction: int
    other_deductions: int
    tax_breakdown: list[TaxDeductionOut] = Field(default_factory=list)
    net_salary: int
    status: str
    issue_date: date | None = None


class MyCompensationOut(APIModel):
    employee_id: str
    employee_name: str
    department: str
    title: str
    base_salary: int
    latest_payslip: PaySlipOut | None = None


class CalculatePayrollRequest(APIModel):
    pay_period_id: str


class CalculatePayrollResponse(APIModel):
    items: list[PaySlipOut]
    total: int


class PayrollProposalOut(APIModel):
    id: str
    employee_id: str
    employee_name: str
    department: str
    pay_period_id: str
    proposed_change_percent: float
    proposed_change_amount: int
    current_salary: int | None = None
    proposed_salary: int | None = None
    prediction_id: str | None = None
    reason: str
    status: str
    decided_at: datetime | None = None
    decision_note: str | None = None


class PayrollProposalDecision(APIModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    decision_note: str | None = Field(default=None, max_length=2000)
