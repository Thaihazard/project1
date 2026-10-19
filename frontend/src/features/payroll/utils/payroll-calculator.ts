import type { IPaySlip } from '../types/payroll.types';

export function calculatePayrollTotals(slips: IPaySlip[]) {
  return slips.reduce(
    (totals, slip) => ({
      employeeCount: totals.employeeCount + 1,
      totalGross: totals.totalGross + slip.grossSalary,
      totalNet: totals.totalNet + slip.netSalary,
      totalTax: totals.totalTax + slip.taxDeduction,
    }),
    { employeeCount: 0, totalGross: 0, totalNet: 0, totalTax: 0 },
  );
}
