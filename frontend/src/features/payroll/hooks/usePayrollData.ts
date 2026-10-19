import { useQuery } from '@tanstack/react-query';
import { getMyCompensation, getMyPaySlip, getPaySlips } from '../api/getPaySlips';

export const payrollKeys = {
  all: ['payroll'] as const,
  slips: (periodId?: string) => [...payrollKeys.all, 'slips', periodId] as const,
  mySlip: (id?: string) => [...payrollKeys.all, 'mine', id] as const,
  myCompensation: ['payroll', 'mine', 'compensation'] as const,
};

export function usePayrollData(payPeriodId?: string) {
  return useQuery({ queryKey: payrollKeys.slips(payPeriodId), queryFn: () => getPaySlips(payPeriodId) });
}

export function useMyPaySlip(paySlipId?: string) {
  return useQuery({ queryKey: payrollKeys.mySlip(paySlipId), queryFn: () => getMyPaySlip(paySlipId), enabled: Boolean(paySlipId) });
}

export function useMyCompensation() {
  return useQuery({ queryKey: payrollKeys.myCompensation, queryFn: getMyCompensation });
}
