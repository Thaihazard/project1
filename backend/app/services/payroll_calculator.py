from app.models.payroll import PaySlip


def recalculate_slip(slip: PaySlip) -> None:
    """Reconcile totals using stored deductions; tax rules are intentionally policy-owned."""
    slip.gross_salary = slip.base_salary + slip.allowances + slip.bonus + slip.overtime_pay
    slip.net_salary = max(0, slip.gross_salary - slip.tax_deduction - slip.insurance_deduction - slip.other_deductions)
