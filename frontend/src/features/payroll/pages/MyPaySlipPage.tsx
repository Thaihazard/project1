import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { PaySlipDetailModal } from '../components/PaySlipDetailModal';
import { PayrollStatusBadge } from '../components/PayrollStatusBadge';
import { useMyCompensation, useMyPaySlip } from '../hooks/usePayrollData';

const money = (amount: number) => new Intl.NumberFormat('vi-VN').format(amount) + ' ₫';

export default function MyPaySlipPage() {
  const { paySlipId } = useParams<{ paySlipId: string }>();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const compensation = useMyCompensation();
  const selectedSlip = useMyPaySlip(paySlipId);
  const slip = paySlipId ? selectedSlip.data : compensation.data?.latestPayslip ?? undefined;

  if (paySlipId ? selectedSlip.isLoading : compensation.isLoading) return <p className="p-6">Đang tải thông tin lương…</p>;
  if (paySlipId ? selectedSlip.isError : compensation.isError) return <p role="alert" className="p-6 text-rose-700">Không thể tải thông tin lương. Hãy thử tải lại trang hoặc kiểm tra kết nối backend.</p>;

  if (!paySlipId && compensation.data && !slip) {
    return <main className="mx-auto max-w-3xl space-y-5 p-6">
      <section className="rounded-2xl border bg-white p-6">
        <h1 className="text-2xl font-bold">Lương của tôi</h1>
        <p className="mt-2 text-slate-500">{compensation.data.employeeName} · {compensation.data.employeeId}</p>
        <p className="mt-6 text-sm text-slate-500">Lương cơ bản theo hồ sơ</p>
        <p className="text-3xl font-bold text-indigo-700">{money(compensation.data.baseSalary)} <span className="text-sm font-normal text-slate-500">/ tháng</span></p>
      </section>
      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950">
        Chưa có phiếu lương cho bạn. HR cần chọn kỳ lương và bấm <b>Tính lương</b> để tạo phiếu nháp. Lương cơ bản ở trên là mức trong hồ sơ, chưa phải số tiền thực nhận.
      </section>
    </main>;
  }

  if (!slip) return <p role="alert" className="p-6 text-rose-700">Không tìm thấy phiếu lương này.</p>;

  return <main className="mx-auto max-w-3xl p-6"><div className="rounded-2xl border bg-white p-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-bold">Phiếu lương của tôi</h1><p className="mt-2 text-slate-500">{slip.payPeriodName ?? slip.payPeriodId}</p></div><PayrollStatusBadge status={slip.status} /></div>
    <p className="mt-6 text-sm text-slate-500">Thực nhận</p><p className="text-3xl font-bold text-indigo-700">{money(slip.netSalary)}</p>
    <section aria-label="Tóm tắt phiếu lương" className="mt-6 rounded-xl bg-slate-50 p-4"><h2 className="mb-3 text-sm font-semibold text-slate-800">Tóm tắt thu nhập</h2><dl className="space-y-2 text-sm">
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Lương cơ bản</dt><dd className="font-medium text-slate-900">{money(slip.baseSalary)}</dd></div>
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Phụ cấp</dt><dd className="font-medium text-slate-900">{money(slip.allowances)}</dd></div>
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Thưởng KPI / thưởng khác</dt><dd className="font-medium text-slate-900">{money(slip.bonus)}</dd></div>
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Tiền làm thêm</dt><dd className="font-medium text-slate-900">{money(slip.overtimePay)}</dd></div>
      <div className="flex justify-between gap-4 border-t pt-2 font-semibold"><dt className="text-slate-700">Tổng thu nhập</dt><dd className="text-slate-900">{money(slip.grossSalary)}</dd></div>
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Khấu trừ thuế TNCN</dt><dd className="font-medium text-rose-700">−{money(slip.taxDeduction)}</dd></div>
      <div className="flex justify-between gap-4"><dt className="text-slate-600">Khấu trừ bảo hiểm</dt><dd className="font-medium text-rose-700">−{money(slip.insuranceDeduction)}</dd></div>
      {slip.otherDeductions > 0 && <div className="flex justify-between gap-4"><dt className="text-slate-600">Khoản khấu trừ khác</dt><dd className="font-medium text-rose-700">−{money(slip.otherDeductions)}</dd></div>}
    </dl></section>
    <button className="mt-5 rounded-lg bg-indigo-600 px-4 py-2 text-white" onClick={() => setDetailsOpen(true)}>Xem chi tiết</button>
    <PaySlipDetailModal paySlip={detailsOpen ? slip : null} onClose={() => setDetailsOpen(false)} />
  </div></main>;
}
