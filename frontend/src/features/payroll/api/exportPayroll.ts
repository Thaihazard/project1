import api from '@/lib/axios';

export async function exportPayroll(payPeriodId: string): Promise<void> {
  const { data } = await api.get<Blob>('/payroll/export', {
    params: { payPeriodId }, responseType: 'blob',
  });
  const url = URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.download = `payroll-${payPeriodId}.xlsx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
