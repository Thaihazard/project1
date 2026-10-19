import api from '@/lib/axios';
import type { IPaySlip } from '../types/payroll.types';

export interface IMyCompensation {
  employeeId: string;
  employeeName: string;
  department: string;
  title: string;
  baseSalary: number;
  latestPayslip: IPaySlip | null;
}

export async function getPaySlips(payPeriodId?: string): Promise<IPaySlip[]> {
  const { data } = await api.get<IPaySlip[]>('/payroll/payslips', {
    params: payPeriodId ? { payPeriodId } : undefined,
  });
  return data;
}

export async function getMyPaySlip(paySlipId?: string): Promise<IPaySlip> {
  const path = paySlipId
    ? `/payroll/me/payslips/${encodeURIComponent(paySlipId)}`
    : '/payroll/me/payslips/latest';
  const { data } = await api.get<IPaySlip>(path);
  return data;
}

export async function getMyCompensation(): Promise<IMyCompensation> {
  const { data } = await api.get<IMyCompensation>('/payroll/me/compensation');
  return data;
}
