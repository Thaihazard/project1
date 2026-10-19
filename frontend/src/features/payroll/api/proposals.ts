import api from '@/lib/axios';

export interface PayrollProposal {
  id: string;
  employeeId: string;
  employeeName: string;
  department: string;
  payPeriodId: string;
  proposedChangePercent: number;
  proposedChangeAmount: number;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  decidedAt: string | null;
}

export async function getPayrollProposals() {
  const { data } = await api.get<PayrollProposal[]>('/payroll/proposals');
  return data;
}

export async function decidePayrollProposal(proposalId: string, decision: 'approved' | 'rejected') {
  const { data } = await api.post<PayrollProposal>(`/payroll/proposals/${encodeURIComponent(proposalId)}/decision`, { decision });
  return data;
}
