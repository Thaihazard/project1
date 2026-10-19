import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { exportPayroll } from '../api/exportPayroll';
import { PaySlipDetailModal } from '../components/PaySlipDetailModal';
import { PayrollSummaryCards } from '../components/PayrollSummaryCards';
import { PayrollStatusBadge } from '../components/PayrollStatusBadge';
import { useCalculateSalary } from '../hooks/useCalculateSalary';
import { payrollKeys, usePayrollData } from '../hooks/usePayrollData';
import { calculatePayrollTotals } from '../utils/payroll-calculator';
import type { IPaySlip } from '../types/payroll.types';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/axios';

const money = (amount: number) => new Intl.NumberFormat('vi-VN').format(amount) + ' ₫';

export const PayrollListPage = () => {
  const [periodId, setPeriodId] = useState('');
  const [selectedSlip, setSelectedSlip] = useState<IPaySlip | null>(null);
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const { data: slips = [], isLoading, isError, error } = usePayrollData(periodId || undefined);
  const calculate = useCalculateSalary();
  const approve = useMutation({
    mutationFn: async (id: string) => api.post(`/payroll/periods/${encodeURIComponent(id)}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: payrollKeys.all }),
  });
  const periods = useMemo(() => [...new Map(slips.map((slip) => [slip.payPeriodId, slip.payPeriodName ?? slip.payPeriodId])).entries()], [slips]);
  const summary = useMemo(() => calculatePayrollTotals(slips), [slips]);

  return <main className="mx-auto max-w-7xl space-y-6 p-6">
    <header className="flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-2xl font-bold">Quản lý bảng lương</h1><p className="mt-1 text-sm text-slate-500">Theo dõi phiếu lương và tổng hợp kỳ lương.</p></div>
      <div className="flex flex-wrap gap-2"><select aria-label="Kỳ lương" className="rounded-lg border border-slate-300 bg-white px-3 py-2" value={periodId} onChange={(event) => setPeriodId(event.target.value)}><option value="">Tất cả kỳ lương</option>{periods.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select>
        {user?.role === 'hr' && <button disabled={!periodId || calculate.isPending} onClick={() => calculate.mutate({ payPeriodId: periodId })} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{calculate.isPending ? 'Đang tính…' : 'Tính lương'}</button>}
        {user?.role === 'hr' && periodId && slips.some((slip) => slip.status === 'draft') && <button disabled={approve.isPending} onClick={() => { if (window.confirm('Duyệt và khóa trạng thái các phiếu lương Nháp trong kỳ này?')) approve.mutate(periodId); }} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{approve.isPending ? 'Đang duyệt…' : 'Duyệt kỳ lương'}</button>}
        {user?.role === 'hr' && <button disabled={!periodId} onClick={() => periodId && exportPayroll(periodId)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold disabled:opacity-50">Xuất Excel</button>}</div>
    </header>
    {isLoading ? <p role="status">Đang tải dữ liệu lương…</p> : null}
    {isError ? <p role="alert" className="rounded-lg bg-rose-50 p-4 text-rose-700">Không thể tải dữ liệu lương: {(error as Error).message}</p> : null}
    {calculate.isError ? <p role="alert" className="rounded-lg bg-rose-50 p-4 text-rose-700">Không thể tính lương. Vui lòng thử lại.</p> : null}
    {calculate.isSuccess ? <p role="status" className="rounded-lg bg-emerald-50 p-4 text-emerald-700">Đã gửi yêu cầu tính lương.</p> : null}
    {approve.isError ? <p role="alert" className="rounded-lg bg-rose-50 p-4 text-rose-700">Không duyệt được kỳ lương. Hãy tải lại và kiểm tra trạng thái các phiếu.</p> : null}
    {approve.isSuccess ? <p role="status" className="rounded-lg bg-emerald-50 p-4 text-emerald-700">Đã duyệt các phiếu lương của kỳ.</p> : null}
    {user?.role === 'hr' && <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950">Thuế TNCN và bảo hiểm hiện lấy từ các khoản đã ghi trên phiếu lương. Hãy xác nhận chính sách khấu trừ, giảm trừ và giờ OT đã duyệt trước khi tính/chốt; hệ thống chưa tự áp dụng công thức pháp lý.</p>}
    {user?.role === 'hr' && !periodId && <p className="rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-900">Các phiếu đang ở trạng thái <b>Nháp</b> chưa được duyệt. Chọn một kỳ lương ở góc trên để tính lại, xuất Excel hoặc duyệt kỳ.</p>}
    {!isLoading && !isError && <><PayrollSummaryCards summary={summary} />
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Nhân viên</th><th className="p-4">Kỳ lương</th><th className="p-4">Tổng thu nhập</th><th className="p-4">Thuế</th><th className="p-4">Thực nhận</th><th className="p-4">Trạng thái</th><th className="p-4">Chi tiết</th></tr></thead><tbody className="divide-y divide-slate-100">{slips.map((slip) => <tr key={slip.id}><td className="p-4"><div className="font-medium">{slip.employeeName}</div><div className="text-xs text-slate-500">{slip.employeeId}</div></td><td className="p-4">{slip.payPeriodName ?? slip.payPeriodId}</td><td className="p-4">{money(slip.grossSalary)}</td><td className="p-4">{money(slip.taxDeduction)}</td><td className="p-4 font-semibold">{money(slip.netSalary)}</td><td className="p-4"><PayrollStatusBadge status={slip.status} /></td><td className="p-4"><button className="text-indigo-700 hover:underline" onClick={() => setSelectedSlip(slip)}>Xem</button> <Link className="ml-2 text-indigo-700 hover:underline" to={`/payroll/${encodeURIComponent(slip.payPeriodId)}/detail`}>Kỳ lương</Link></td></tr>)}</tbody></table>
      {!slips.length && <p className="p-6 text-center text-slate-500">Chưa có phiếu lương cho kỳ này.</p>}</div>
    </>}
    <PaySlipDetailModal paySlip={selectedSlip} onClose={() => setSelectedSlip(null)} />
  </main>;
};
