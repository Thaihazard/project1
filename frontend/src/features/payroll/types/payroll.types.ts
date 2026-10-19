export type PayrollStatus = 'draft' | 'processing' | 'approved' | 'paid';

export interface ITaxDeduction {
  name: string;
  amount: number;
}

export interface IPayPeriod {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  status: PayrollStatus;
}

export interface IPaySlip {
  id: string;
  employeeId: string;
  employeeName: string;
  department?: string;
  payPeriodId: string;
  payPeriodName?: string;
  baseSalary: number;
  allowances: number;
  bonus: number;
  overtimePay: number;
  grossSalary: number;
  taxDeduction: number;
  insuranceDeduction: number;
  otherDeductions: number;
  taxBreakdown?: ITaxDeduction[];
  netSalary: number;
  status: PayrollStatus;
  issueDate?: string;
}

export interface IPayrollSummary {
  employeeCount: number;
  totalGross: number;
  totalNet: number;
  totalTax: number;
}

export interface ICalculatePayrollRequest {
  payPeriodId: string;
}
