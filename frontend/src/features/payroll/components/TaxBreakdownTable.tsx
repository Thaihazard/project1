import type { ITaxDeduction } from '../types/payroll.types';

const money = (amount: number) => new Intl.NumberFormat('vi-VN').format(amount) + ' ₫';

export function TaxBreakdownTable({ deductions }: { deductions: ITaxDeduction[] }) {
  if (!deductions.length) return <p className="text-sm text-slate-500">Chưa có dữ liệu chi tiết khấu trừ thuế.</p>;
  return <table className="w-full text-left text-sm">
    <thead><tr className="border-b text-slate-500"><th className="py-2">Khoản khấu trừ</th><th className="py-2 text-right">Số tiền</th></tr></thead>
    <tbody>{deductions.map((item, index) => <tr className="border-b last:border-0" key={`${item.name}-${index}`}>
      <td className="py-2">{item.name}</td><td className="py-2 text-right">{money(item.amount)}</td>
    </tr>)}</tbody>
  </table>;
}
