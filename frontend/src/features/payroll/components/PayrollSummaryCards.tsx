import type { IPayrollSummary } from '../types/payroll.types';

const money = (amount: number) => new Intl.NumberFormat('vi-VN').format(amount) + ' ₫';

export function PayrollSummaryCards({ summary }: { summary: IPayrollSummary }) {
  const cards = [
    ['Nhân viên', summary.employeeCount.toLocaleString('vi-VN')],
    ['Tổng quỹ lương', money(summary.totalGross)],
    ['Thực nhận', money(summary.totalNet)],
    ['Thuế TNCN', money(summary.totalTax)],
  ];
  return <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Tổng quan kỳ lương">
    {cards.map(([label, value]) => <article key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-bold text-slate-900">{value}</p>
    </article>)}
  </section>;
}
