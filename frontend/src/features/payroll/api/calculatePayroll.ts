import api from '@/lib/axios';
import type { ICalculatePayrollRequest, IPaySlip } from '../types/payroll.types';

export async function calculatePayroll(request: ICalculatePayrollRequest): Promise<IPaySlip[]> {
  const { data } = await api.post<IPaySlip[]>('/payroll/calculate', request);
  return data;
}
