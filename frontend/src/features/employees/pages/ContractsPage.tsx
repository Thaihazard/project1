import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '@/lib/axios';
import { useAuthStore } from '@/store/useAuthStore';

interface Contract { id: string; employeeId: string; employeeName: string; contractType: string; startDate: string; endDate: string | null; baseSalary: number; status: string }
const money = (value: number) => new Intl.NumberFormat('vi-VN').format(value) + ' ₫';

export default function ContractsPage() {
  const user = useAuthStore((state) => state.user);
  const isHr = user?.role === 'hr';
  const client = useQueryClient();
  const [employeeId, setEmployeeId] = useState('');
  const [contractType, setContractType] = useState('Fixed-term');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [baseSalary, setBaseSalary] = useState('');
  const query = useQuery({ queryKey: ['contracts', isHr || user?.role === 'manager' ? 'team' : 'me'], queryFn: async () => (await api.get<Contract[]>(isHr || user?.role === 'manager' ? '/contracts' : '/contracts/me')).data });
  const create = useMutation({ mutationFn: async () => (await api.post('/contracts', { employeeId, contractType, startDate, endDate: endDate || null, baseSalary: Number(baseSalary) })).data, onSuccess: () => { setEmployeeId(''); setBaseSalary(''); client.invalidateQueries({ queryKey: ['contracts'] }); } });
  function submit(event: FormEvent) { event.preventDefault(); create.mutate(); }
  return <main className="mx-auto max-w-5xl space-y-6 p-6"><header><Link to="/" className="text-sm text-indigo-700">← AI CompHub</Link><h1 className="mt-3 text-2xl font-bold">Hợp đồng lao động</h1><p className="mt-1 text-sm text-slate-500">Theo dõi loại hợp đồng, thời hạn và mức lương theo hợp đồng.</p></header>
    {isHr && <form onSubmit={submit} className="grid gap-3 rounded-2xl border bg-white p-5 md:grid-cols-3"><h2 className="font-semibold md:col-span-3">Tạo hồ sơ hợp đồng</h2><label className="text-sm">Mã nhân viên<input required value={employeeId} onChange={(event) => setEmployeeId(event.target.value)} placeholder="EMP-1001" className="mt-1 block w-full rounded-lg border p-2" /></label><label className="text-sm">Loại hợp đồng<select value={contractType} onChange={(event) => setContractType(event.target.value)} className="mt-1 block w-full rounded-lg border p-2"><option>Fixed-term</option><option>Indefinite</option><option>Probation</option><option>Seasonal</option></select></label><label className="text-sm">Lương theo hợp đồng<input required type="number" min="1" value={baseSalary} onChange={(event) => setBaseSalary(event.target.value)} className="mt-1 block w-full rounded-lg border p-2" /></label><label className="text-sm">Ngày bắt đầu<input required type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="mt-1 block w-full rounded-lg border p-2" /></label><label className="text-sm">Ngày kết thúc (nếu có)<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="mt-1 block w-full rounded-lg border p-2" /></label><div className="flex items-end"><button disabled={create.isPending} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">Lưu hợp đồng</button></div>{create.isError && <p role="alert" className="text-sm text-rose-700 md:col-span-3">Không tạo được hợp đồng; kiểm tra mã nhân viên và dữ liệu.</p>}</form>}
    <section className="overflow-hidden rounded-2xl border bg-white"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Nhân viên</th><th className="p-4">Loại hợp đồng</th><th className="p-4">Thời hạn</th><th className="p-4">Lương theo hợp đồng</th><th className="p-4">Trạng thái</th></tr></thead><tbody className="divide-y">{(query.data ?? []).map((item) => <tr key={item.id}><td className="p-4">{item.employeeName}<small className="block text-slate-500">{item.employeeId}</small></td><td className="p-4">{item.contractType}</td><td className="p-4">{item.startDate} – {item.endDate ?? 'Không thời hạn'}</td><td className="p-4">{money(item.baseSalary)}</td><td className="p-4"><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">{item.status === 'active' ? 'Hiệu lực' : item.status}</span></td></tr>)}</tbody></table></div>{!query.isLoading && !query.data?.length && <p className="p-8 text-center text-sm text-slate-500">Chưa có hợp đồng.</p>}</section>
  </main>;
}
