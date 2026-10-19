import type { PayrollStatus } from '../types/payroll.types';

const statusLabels: Record<PayrollStatus, string> = {
  draft: 'Nháp',
  processing: 'Đang xử lý',
  approved: 'Đã duyệt',
  paid: 'Đã thanh toán',
};

const statusStyles: Record<PayrollStatus, string> = {
  draft: 'bg-amber-100 text-amber-800',
  processing: 'bg-blue-100 text-blue-800',
  approved: 'bg-emerald-100 text-emerald-800',
  paid: 'bg-indigo-100 text-indigo-800',
};

export function PayrollStatusBadge({ status }: { status: PayrollStatus }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyles[status]}`}>{statusLabels[status]}</span>;
}
