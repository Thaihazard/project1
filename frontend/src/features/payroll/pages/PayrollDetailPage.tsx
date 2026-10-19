import { useParams } from 'react-router-dom';
import { usePayrollData } from '../hooks/usePayrollData';
import { calculatePayrollTotals } from '../utils/payroll-calculator';
import { PayrollSummaryCards } from '../components/PayrollSummaryCards';

export default function PayrollDetailPage() {
  const { periodId } = useParams<{ periodId: string }>();
  const { data: slips = [], isLoading, isError } = usePayrollData(periodId);
  if (isLoading) return <p className="p-6">Đang tải bảng lương…</p>;
  if (isError) return <p role="alert" className="p-6 text-rose-700">Không thể tải bảng lương kỳ này.</p>;
  return <main className="mx-auto max-w-7xl space-y-6 p-6"><h1 className="text-2xl font-bold">Chi tiết kỳ lương {periodId}</h1><PayrollSummaryCards summary={calculatePayrollTotals(slips)} /><div className="rounded-xl border bg-white p-5"><h2 className="mb-4 font-semibold">Phiếu lương nhân viên ({slips.length})</h2><ul className="divide-y">{slips.map((slip) => <li key={slip.id} className="flex justify-between py-3"><span>{slip.employeeName} · {slip.employeeId}</span><strong>{new Intl.NumberFormat('vi-VN').format(slip.netSalary)} ₫</strong></li>)}</ul></div></main>;
}
