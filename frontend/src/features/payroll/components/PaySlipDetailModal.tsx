import type { IPaySlip } from '../types/payroll.types';
import { TaxBreakdownTable } from './TaxBreakdownTable';

const money = (amount: number) => new Intl.NumberFormat('vi-VN').format(amount) + ' ₫';

export function PaySlipDetailModal({ paySlip, onClose }: { paySlip: IPaySlip | null; onClose: () => void }) {
  if (!paySlip) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section role="dialog" aria-modal="true" aria-labelledby="payslip-title" className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
      <div className="flex items-start justify-between"><div><h2 id="payslip-title" className="text-xl font-bold">Phiếu lương: {paySlip.employeeName}</h2><p className="mt-1 text-sm text-slate-500">{paySlip.payPeriodName ?? paySlip.payPeriodId}</p></div><button className="rounded-lg px-3 py-1 text-slate-500 hover:bg-slate-100" onClick={onClose} aria-label="Đóng">✕</button></div>
      <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
        <div><dt className="text-slate-500">Lương cơ bản</dt><dd className="mt-1 font-medium">{money(paySlip.baseSalary)}</dd></div>
        <div><dt className="text-slate-500">Phụ cấp</dt><dd className="mt-1 font-medium">{money(paySlip.allowances)}</dd></div>
        <div><dt className="text-slate-500">Thưởng</dt><dd className="mt-1 font-medium">{money(paySlip.bonus)}</dd></div>
        <div><dt className="text-slate-500">Làm thêm giờ</dt><dd className="mt-1 font-medium">{money(paySlip.overtimePay)}</dd></div>
        <div><dt className="text-slate-500">Tổng thu nhập</dt><dd className="mt-1 font-medium">{money(paySlip.grossSalary)}</dd></div>
        <div><dt className="text-slate-500">Bảo hiểm</dt><dd className="mt-1 font-medium">{money(paySlip.insuranceDeduction)}</dd></div>
        <div><dt className="text-slate-500">Thuế TNCN</dt><dd className="mt-1 font-medium">{money(paySlip.taxDeduction)}</dd></div>
        <div><dt className="text-slate-500">Thực nhận</dt><dd className="mt-1 font-bold text-indigo-700">{money(paySlip.netSalary)}</dd></div>
      </dl>
      <div className="mt-6"><h3 className="mb-2 font-semibold">Chi tiết thuế TNCN</h3><TaxBreakdownTable deductions={paySlip.taxBreakdown ?? []} /></div>
    </section>
  </div>;
}
