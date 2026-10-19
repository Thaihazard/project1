import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BrainCircuit, HelpCircle, ShieldCheck, Wallet, BarChart3, SlidersHorizontal, GraduationCap, Users, Check, X, PieChart, LockKeyhole } from 'lucide-react';
import { predictSalary, simulateBudget } from '../api/aiSalary';
import { useAuthStore } from '@/store/useAuthStore';
import { decidePayrollProposal, getPayrollProposals } from '@/features/payroll/api/proposals';
import { getMyCompensation } from '@/features/payroll/api/getPaySlips';
import { Link } from 'react-router-dom';
import { API_DOCS_URL } from '@/config/env.config';

type Role = 'employee' | 'manager' | 'hr';
const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(Math.round(n)) + ' ₫';
const masked = '••••••••';
const Tip = ({ children }: { children: string }) => <span title={children} aria-label={children} className="ml-1 inline-flex cursor-help text-slate-400"><HelpCircle size={14} /></span>;
const Heading = ({ title, subtitle }: { title: string; subtitle: string }) => <div><h2 className="text-xl font-bold text-slate-900">{title}</h2><p className="mt-1 text-sm text-slate-500">{subtitle}</p></div>;
const Metric = ({ title, value, caption }: { title: string; value: string; caption: string }) => <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{title}</p><p className="mt-3 text-2xl font-bold text-slate-900">{value}</p><p className="mt-1 text-xs text-slate-500">{caption}</p></article>;

function LoginRequiredModal({ onClose }: { onClose: () => void }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section role="dialog" aria-modal="true" aria-labelledby="login-required-title" className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-start justify-between gap-4"><div className="rounded-xl bg-indigo-50 p-3 text-indigo-700"><LockKeyhole size={22} /></div><button type="button" onClick={onClose} aria-label="Đóng" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={18} /></button></div>
      <h2 id="login-required-title" className="mt-4 text-xl font-bold text-slate-900">Đăng nhập để tiếp tục</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Tính năng này chỉ dành cho người dùng được phân quyền. Đăng nhập để xem dữ liệu phù hợp với vai trò của bạn.</p>
      <div className="mt-6 flex justify-end gap-3"><button type="button" onClick={onClose} className="rounded-lg border px-4 py-2 text-sm font-semibold text-slate-700">Để sau</button><a href="/login" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">Đăng nhập</a></div>
    </section>
  </div>;
}

function Employee() {
  const [kpi, setKpi] = useState(88);
  const [pmp, setPmp] = useState(false);
  const [skills, setSkills] = useState(4.2);
  const aiPrediction = useMutation({ mutationFn: predictSalary });
  const user = useAuthStore((state) => state.user);
  const isEmployee = user?.role === 'employee';
  const compensationQuery = useQuery({ queryKey: ['payroll', 'mine', 'compensation'], queryFn: getMyCompensation, enabled: isEmployee });
  if (!isEmployee) return <section className="rounded-3xl border border-indigo-100 bg-white p-8 shadow-sm sm:p-12"><p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Employee portal</p><h2 className="mt-3 text-3xl font-bold text-slate-900">Chào bạn</h2><p className="mt-3 max-w-2xl text-slate-600">Đăng nhập bằng tài khoản nhân viên để xem phiếu lương và dự báo thu nhập cá nhân.</p><a href="/login" className="mt-6 inline-flex rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white">Đăng nhập</a></section>;
  if (compensationQuery.isLoading) return <p role="status" className="rounded-2xl border bg-white p-6 text-sm text-slate-600">Đang tải thông tin nhân sự và lương của bạn…</p>;
  if (compensationQuery.isError || !compensationQuery.data) return <p role="alert" className="rounded-2xl border bg-rose-50 p-6 text-sm text-rose-700">Không tải được thông tin tổng quan. Hãy tải lại trang hoặc kiểm tra backend.</p>;
  const compensation = compensationQuery.data;
  const paySlip = compensation.latestPayslip;
  const base = paySlip?.grossSalary ?? compensation.baseSalary;
  const estimate = base + (kpi - 88) * 180_000 + (pmp ? 2_400_000 : 0) + (skills - 4.2) * 1_000_000;
  const change = ((estimate / base) - 1) * 100;
  const factors = [['KPI gần nhất', '+2,4 triệu', 75], ['Kỹ năng cốt lõi', '+1,8 triệu', 58], ['Chứng chỉ chuyên môn', pmp ? '+2,4 triệu' : '−1,2 triệu', 42], ['Tham chiếu thị trường', '+0,9 triệu', 30]];
  return <div className="space-y-6">
    <section className="rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-indigo-800 p-8 text-white shadow-xl">
      <div className="text-xs font-semibold uppercase tracking-widest text-indigo-200">Cổng thông tin nhân viên · Dự báo 2027</div><h2 className="mt-4 text-3xl font-bold">Chào {compensation.employeeName}</h2><p className="mt-2 text-indigo-100">{compensation.title} · {compensation.department}</p>
      <div className="mt-8 grid gap-6 sm:grid-cols-3"><div><p className="text-xs text-indigo-200">{paySlip ? 'Tổng thu nhập kỳ gần nhất' : 'Lương cơ bản theo hồ sơ'}</p><p className="mt-2 text-2xl font-bold">{fmt(base)}<small className="text-sm font-normal"> / tháng</small></p></div><div><p className="text-xs text-indigo-200">Kỳ lương</p><p className="mt-2 text-2xl font-bold">{paySlip?.payPeriodName || 'Chưa có phiếu lương'}</p></div><p className="flex items-center gap-2 text-sm text-indigo-100"><ShieldCheck size={18} /> Mức lương chỉ thay đổi sau khi được phê duyệt.</p></div>
    </section>
    {!paySlip && <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950">Bạn đang xem lương cơ bản trong hồ sơ. Phiếu lương và số tiền thực nhận sẽ hiện sau khi HR tính kỳ lương. <Link to="/my-pay-slip" className="font-semibold underline">Xem thông tin lương</Link></section>}
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><Heading title="Yếu tố ảnh hưởng thu nhập" subtitle="SHAP breakdown giải thích các tín hiệu của mô hình." /><BarChart3 className="text-indigo-600" /></div>
        <div className="mt-6 space-y-5">{factors.map(([name, value, width]) => <div key={String(name)}><div className="mb-2 flex justify-between text-sm"><span>{name}<Tip>Đóng góp mô hình, không phải khoản lương cộng trực tiếp.</Tip></span><strong className="text-emerald-700">{value}</strong></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-emerald-500" style={{ width: width + '%' }} /></div></div>)}</div>
        <p className="mt-5 text-xs text-slate-500">Ước lượng tham khảo dựa trên dữ liệu và kỳ đánh giá gần nhất.</p>
      </section>
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><Heading title="Mô phỏng What-If" subtitle="Thay đổi giả định để xem ước lượng phản hồi tức thì." /><SlidersHorizontal className="text-indigo-600" /></div>
        <label className="mt-6 block text-sm">KPI mục tiêu <b className="float-right text-indigo-700">{kpi}%</b><input aria-label="KPI mục tiêu" className="mt-3 w-full accent-indigo-600" type="range" min="70" max="120" value={kpi} onChange={e => setKpi(+e.target.value)} /></label>
        <label className="mt-5 flex items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={pmp} onChange={e => setPmp(e.target.checked)} className="accent-indigo-600" /> Hoàn thành chứng chỉ PMP <span className="ml-auto text-xs text-slate-500">Giả định</span></label>
        <label className="mt-5 block text-sm">Năng lực <b className="float-right text-indigo-700">{skills.toFixed(1)} / 5</b><input aria-label="Điểm năng lực" className="mt-3 w-full accent-indigo-600" type="range" min="3" max="5" step=".1" value={skills} onChange={e => setSkills(+e.target.value)} /></label>
        <div aria-live="polite" className="mt-6 rounded-xl bg-indigo-50 p-4"><p className="text-xs text-indigo-700">Ước lượng kịch bản</p><div className="mt-1 flex items-baseline justify-between"><strong className="text-2xl text-indigo-950">{fmt(estimate)}</strong><b className="text-emerald-700">+{change.toFixed(1)}%</b></div><p className="mt-2 text-xs text-indigo-700">Mô phỏng này không cập nhật hồ sơ hoặc lương.</p></div>
        <button disabled={aiPrediction.isPending} onClick={() => aiPrediction.mutate({ currentSalary: base, kpiScore: kpi, softSkillScore: skills, yearsExperience: 8, certificationCount: pmp ? 1 : 0 })} className="mt-3 rounded-lg border border-indigo-200 px-3 py-2 text-xs font-semibold text-indigo-700 disabled:opacity-50">{aiPrediction.isPending ? 'Đang gọi AI service…' : 'Lấy dự báo từ AI service'}</button>
        {aiPrediction.isError && <p role="alert" className="mt-2 text-xs text-rose-700">Không thể lấy dự báo từ backend.</p>}
        {aiPrediction.data && <div className="mt-3 rounded-lg border border-slate-200 p-3 text-xs"><p className="font-semibold">Backend estimate ({aiPrediction.data.modelVersion})</p><p className="mt-1">{fmt(aiPrediction.data.minSalary)} – {fmt(aiPrediction.data.maxSalary)} · Trung vị {fmt(aiPrediction.data.medianSalary)}</p><p className="mt-2 text-slate-500">{aiPrediction.data.disclaimer}</p></div>}
      </section>
    </div>
    <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><Heading title="Lộ trình phát triển gợi ý" subtitle="Ưu tiên học tập để phát triển kỹ năng và cơ hội nghề nghiệp." /><GraduationCap className="text-indigo-600" /></div><div className="mt-5 grid gap-3 md:grid-cols-3">{[['Chứng chỉ PMP','Quản lý dự án · 8 tuần','Tác động dự kiến: cao'],['Cloud architecture','Thiết kế hệ thống · 6 tuần','Tác động dự kiến: cao'],['Mentoring','Năng lực dẫn dắt · 4 tuần','Tác động dự kiến: vừa']].map(([title, detail, impact]) => <article key={title} className="rounded-xl border p-4"><h3 className="font-semibold">{title}</h3><p className="mt-1 text-sm text-slate-500">{detail}</p><p className="mt-3 text-xs font-semibold text-emerald-700">{impact}</p></article>)}</div></section>
  </div>;
}

const initial = [
  { name: 'Nhân viên A', role: 'Senior Engineer', kpi: 92, salary: 28_000_000, proposal: 31_000_000, flag: 'Underpaid', line: 'M 2 18 L 18 13 L 34 15 L 50 8 L 66 10 L 82 3' },
  { name: 'Nhân viên B', role: 'Mid Engineer', kpi: 74, salary: 22_000_000, proposal: 19_500_000, flag: 'Overpaid', line: 'M 2 3 L 18 8 L 34 7 L 50 13 L 66 12 L 82 20' },
  { name: 'Nhân viên C', role: 'Senior Engineer', kpi: 89, salary: 29_500_000, proposal: 30_000_000, flag: 'Trong dải', line: 'M 2 15 L 18 11 L 34 13 L 50 8 L 66 9 L 82 5' },
];
function Manager({ isManager, onRequireLogin }: { isManager: boolean; onRequireLogin: () => void }) {
  const [message, setMessage] = useState('');
  const [level, setLevel] = useState('Senior');
  const rows = level === 'Senior' ? [initial[0], initial[2]] : [initial[1]];
  const action = (name: string, text: string) => {
    if (!isManager) return onRequireLogin();
    setMessage(text + name + '. Đề xuất cần được duyệt trước khi cập nhật lương.');
  };
  return <div className="space-y-6"><div><p className="text-xs font-bold uppercase tracking-widest text-indigo-600">Manager dashboard</p><Heading title="Hiệu suất và công bằng trong nhóm" subtitle="Tổng quan nhân sự trực thuộc, xu hướng hiệu suất và đề xuất cần xem xét." /></div>
    <div className="grid gap-4 sm:grid-cols-3"><Metric title="Nhân sự trực thuộc" value={isManager ? '18' : '—'} caption={isManager ? 'Dữ liệu minh họa' : 'Đăng nhập để xem'} /><Metric title="Hiệu suất trung bình" value={isManager ? '84 / 100' : '—'} caption={isManager ? 'Dữ liệu minh họa' : 'Đăng nhập để xem'} /><Metric title="Đề xuất cần xem" value={isManager ? '5' : '—'} caption={isManager ? 'Dữ liệu minh họa' : 'Đăng nhập để xem'} /></div>
    {message && <div role="status" className="flex justify-between rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">{message}<button onClick={() => setMessage('')} aria-label="Đóng"><X size={16} /></button></div>}
    <section className="overflow-x-auto rounded-2xl border bg-white shadow-sm"><div className="flex items-center justify-between p-5"><Heading title="Team overview" subtitle={isManager ? 'Dữ liệu minh họa · đề xuất AI cần được quản lý xác minh.' : 'Dữ liệu ẩn trong chế độ khách. Đăng nhập để xem nhóm của bạn.'} /><Users className="text-indigo-600" /></div><table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr>{['Nhân sự','Xu hướng','KPI','Hiện tại','Gợi ý AI','Cảnh báo','Thao tác'].map(x => <th key={x} className="p-4">{x}</th>)}</tr></thead><tbody className="divide-y">{initial.map(p => <tr key={p.name}><td className="p-4"><b>{isManager ? p.name : 'Nhân viên ẩn danh'}</b><small className="block text-slate-500">{isManager ? p.role : '—'}</small></td><td className="p-4">{isManager ? <svg viewBox="0 0 84 24" className="h-8 w-20" aria-label={'Xu hướng ' + p.name}><path d={p.line} fill="none" stroke={p.flag === 'Overpaid' ? '#f59e0b' : '#6366f1'} strokeWidth="2.5" /></svg> : '—'}</td><td className="p-4">{isManager ? p.kpi : '—'}</td><td className="p-4">{isManager ? fmt(p.salary) : masked}</td><td className="p-4 font-semibold text-indigo-700">{isManager ? fmt(p.proposal) : masked} <Tip>Ước tính minh họa, cần xác minh.</Tip></td><td className="p-4"><span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (p.flag === 'Underpaid' ? 'bg-rose-50 text-rose-700' : p.flag === 'Overpaid' ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-700')}>{isManager ? p.flag : 'Demo'}</span></td><td className="p-4">{p.flag === 'Underpaid' ? <button onClick={() => action(p.name, 'Đã ghi nhận đề xuất tăng lương cho ')} className="whitespace-nowrap rounded-lg bg-indigo-600 px-3 py-2 text-xs text-white">Đề xuất tăng lương</button> : p.flag === 'Overpaid' ? <button onClick={() => action(p.name, 'Đã ghi nhận kế hoạch cải thiện cho ')} className="whitespace-nowrap rounded-lg border border-amber-300 px-3 py-2 text-xs text-amber-900">Lập kế hoạch PIP</button> : <span className="text-slate-400">—</span>}</td></tr>)}</tbody></table></section>
    <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><Heading title="So sánh cùng cấp bậc" subtitle={isManager ? 'Đối chiếu dữ liệu minh họa giữa các cấp bậc.' : 'Thông tin so sánh được ẩn trong chế độ khách.'} /><select value={level} onChange={e => setLevel(e.target.value)} className="rounded-lg border px-3 py-2"><option>Senior</option><option>Mid</option></select></div><div className="mt-4 grid gap-3 sm:grid-cols-2">{rows.map(p => <div key={p.name} className="rounded-xl border p-4"><div className="flex justify-between"><b>{isManager ? p.name : 'Nhân viên ẩn danh'}</b><span className="text-sm">KPI {isManager ? p.kpi : '—'}</span></div><div className="mt-3 flex justify-between text-sm text-slate-500"><span>Lương</span><b className="text-slate-800">{isManager ? fmt(p.salary) : masked}</b></div><div className="mt-2 flex justify-between text-sm text-slate-500"><span>Gợi ý</span><b className="text-indigo-700">{isManager ? fmt(p.proposal) : masked}</b></div></div>)}</div></section>
  </div>;
}

function HrAdmin({ isHr, onRequireLogin }: { isHr: boolean; onRequireLogin: () => void }) {
  const [kpi, setKpi] = useState(50);
  const [tenure, setTenure] = useState(20);
  const [cycle, setCycle] = useState('Hàng quý');
  const [done, setDone] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const budgetPrediction = useMutation({ mutationFn: simulateBudget });
  const authenticated = isHr;
  const queryClient = useQueryClient();
  const proposalsQuery = useQuery({ queryKey: ['payroll', 'proposals'], queryFn: getPayrollProposals, enabled: authenticated });
  const decisionMutation = useMutation({ mutationFn: ({ id, decision }: { id: string; decision: 'approved' | 'rejected' }) => decidePayrollProposal(id, decision), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payroll', 'proposals'] }), onError: () => setMessage('Không thể lưu quyết định. Kiểm tra kết nối và quyền HR rồi thử lại.') });
  const demoSuggestions = [['DEMO-1','Nhân viên A','Engineering','+10,7%','Dữ liệu minh họa'],['DEMO-2','Nhân viên B','Data Platform','+4,2%','Dữ liệu minh họa'],['DEMO-3','Nhân viên C','Product','+6,0%','Dữ liệu minh họa']];
  const suggestions = authenticated
    ? (proposalsQuery.data ?? []).filter((proposal) => proposal.status === 'pending').map((proposal) => [proposal.id, proposal.employeeName, proposal.department, '+' + proposal.proposedChangePercent.toFixed(1) + '%', proposal.reason])
    : demoSuggestions.filter((item) => !done.includes(item[0]));
  const budget = 4_820_000_000 + (kpi - 40) * 8_200_000 - (tenure - 25) * 3_500_000;
  const finish = (id: string, decision: string) => {
    if (!authenticated) return onRequireLogin();
    if (authenticated) {
      const decisionCode = decision.includes('từ chối') ? 'rejected' : 'approved';
      decisionMutation.mutate({ id, decision: decisionCode });
      setMessage((decisionCode === 'approved' ? 'Đã phê duyệt' : 'Đã từ chối') + ' gợi ý ' + id + '. Mức lương chưa được thay đổi.');
      return;
    }
    setDone([...done, id]);
    setMessage(decision + ' gợi ý ' + id + '. Mức lương chưa được thay đổi.');
  };
  return <div className="space-y-6"><div><p className="text-xs font-bold uppercase tracking-widest text-indigo-600">HR / Quản trị lương</p><Heading title="Quỹ lương, công bằng và quản trị mô hình" subtitle="Vai trò HR phụ trách tính lương, xuất báo cáo và duyệt đề xuất. Phiên bản này chưa định nghĩa vai trò System Admin riêng." /></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric title="Tổng quỹ lương" value={authenticated ? '4,82 tỷ' : masked} caption={authenticated ? 'Dữ liệu minh họa' : 'Đăng nhập HR để xem'} /><Metric title="Quỹ lương mô phỏng" value={authenticated ? (budget / 1e9).toFixed(2) + ' tỷ' : masked} caption={authenticated ? 'Mô phỏng minh họa' : 'Đăng nhập HR để xem'} /><Metric title="Chênh lệch thu nhập" value={authenticated ? '4,8%' : masked} caption={authenticated ? 'Số liệu minh họa' : 'Đăng nhập HR để xem'} /><Metric title="Chờ phê duyệt" value={authenticated ? String(suggestions.length) : '—'} caption="Quyết định của người có thẩm quyền" /></div>
    {message && <div role="status" className="flex justify-between rounded-xl bg-indigo-50 p-4 text-sm text-indigo-800">{message}<button onClick={() => setMessage('')} aria-label="Đóng"><X size={16} /></button></div>}
    <div className="grid gap-6 xl:grid-cols-5"><section className="rounded-2xl border bg-white p-6 shadow-sm xl:col-span-3"><div className="flex justify-between"><Heading title="Phân phối thu nhập theo hiệu suất" subtitle={authenticated ? 'Tổng quan minh họa toàn doanh nghiệp' : 'Đăng nhập HR để xem dữ liệu tổng hợp'} /><PieChart className="text-indigo-600" /></div>{authenticated ? <><div className="mt-7 flex h-44 items-end gap-2 border-b border-l p-3">{[25,38,55,75,92,100,86,66,47,31,18,9].map((h,i) => <div key={i} title={'Nhóm ' + (i+1) + ': ' + h} className="flex-1 rounded-t bg-gradient-to-t from-indigo-600 to-violet-400" style={{height:h+'%'}} />)}</div><div className="mt-2 flex justify-between text-xs text-slate-400"><span>Hiệu suất thấp</span><span>Trung vị</span><span>Hiệu suất cao</span></div><p className="mt-5 text-sm">Dưới dải tham chiếu <b>12%</b><span className="mx-4 text-slate-300">|</span>Trong dải <b>76%</b><span className="mx-4 text-slate-300">|</span>Trên dải <b>12%</b></p></> : <p className="mt-7 rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500">Số liệu phân phối được ẩn trong chế độ khách.</p>}</section>
      <section className="rounded-2xl border bg-white p-6 shadow-sm xl:col-span-2"><div className="flex justify-between"><Heading title="Fairness & bias audit" subtitle={authenticated ? 'Chỉ số minh họa để rà soát sâu hơn.' : 'Đăng nhập HR để xem chỉ số công bằng.'} /><ShieldCheck className="text-emerald-600" /></div>{authenticated ? <div className="mt-6 space-y-5">{[['Chênh lệch theo giới tính','4,8%',48],['Chênh lệch theo thâm niên','7,2%',72],['Độ phủ dữ liệu đánh giá','96%',96]].map(([name,value,width])=><div key={String(name)}><p className="mb-2 flex justify-between text-sm"><span>{name}<Tip>Cần xem cùng vai trò, cấp bậc, thâm niên và trách nhiệm; đây không phải kết luận pháp lý.</Tip></span><b>{value}</b></p><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-amber-400" style={{width:width+'%'}} /></div></div>)}</div> : <p className="mt-6 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500">Các chỉ số nhạy cảm được ẩn trong chế độ khách.</p>}<p className="mt-5 rounded-lg bg-amber-50 p-3 text-xs text-amber-900">Chỉ số cần được HR và pháp chế đánh giá trong bối cảnh dữ liệu đầy đủ.</p></section></div>
    <div className="grid gap-6 xl:grid-cols-2"><section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex justify-between"><Heading title="Budget simulation sandbox" subtitle="Thử thay đổi trọng số và xem quỹ lương ước lượng." /><Wallet className="text-indigo-600" /></div><label className="mt-6 block text-sm">Trọng số KPI <b className="float-right">{kpi}%</b><input aria-label="Trọng số KPI" className="mt-2 w-full accent-indigo-600" type="range" min="20" max={100-tenure} value={kpi} onChange={e=>setKpi(Math.min(+e.target.value,100-tenure))} /></label><label className="mt-5 block text-sm">Trọng số thâm niên <b className="float-right">{tenure}%</b><input aria-label="Trọng số thâm niên" className="mt-2 w-full accent-indigo-600" type="range" min="5" max={100-kpi} value={tenure} onChange={e=>setTenure(Math.min(+e.target.value,100-kpi))} /></label><p className="mt-3 text-xs text-slate-500">Trọng số còn lại: {100-kpi-tenure}%</p><div aria-live="polite" className="mt-4 rounded-xl bg-indigo-50 p-4"><p className="text-xs text-indigo-700">Quỹ lương dự báo · mô phỏng</p><b className="mt-1 block text-2xl text-indigo-950">{authenticated ? fmt(budgetPrediction.data?.projectedBudget ?? budget) : masked}</b><p className="mt-1 text-xs text-indigo-700">{authenticated ? 'Thay đổi ' + fmt((budgetPrediction.data?.projectedBudget ?? budget)-4_820_000_000) + ' so với hiện tại' : 'Đăng nhập HR để xem kết quả mô phỏng.'}</p></div><button disabled={authenticated && budgetPrediction.isPending} onClick={()=>authenticated ? budgetPrediction.mutate({kpiWeight:kpi,tenureWeight:tenure,currentBudget:4_820_000_000}) : onRequireLogin()} className="mt-3 rounded-lg border border-indigo-200 px-3 py-2 text-xs font-semibold text-indigo-700 disabled:opacity-50">{budgetPrediction.isPending?'Đang mô phỏng…':'Tính bằng backend'}</button>{budgetPrediction.isError&&<p role="alert" className="mt-2 text-xs text-rose-700">Không thể mô phỏng. Kiểm tra quyển HR và backend.</p>}<p className="mt-3 text-xs text-slate-500">Số liệu minh họa; cần chạy trên dữ liệu đã được xác minh.</p></section>
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex justify-between"><Heading title="Quản lý cấu hình mô hình" subtitle="Thiết lập lịch chạy và quy trình duyệt." /><BrainCircuit className="text-violet-600" /></div><label className="mt-6 block text-sm font-medium">Chu kỳ chạy AI<select className="mt-2 block w-full rounded-lg border px-3 py-2.5" value={cycle} onChange={e=>setCycle(e.target.value)}><option>Hàng quý</option><option>Hàng năm</option></select></label><div className="mt-5 flex gap-3 rounded-xl border p-4"><LockKeyhole size={17}/><p className="text-xs leading-relaxed text-slate-600">AI chỉ gợi ý. Thay đổi lương cần qua quy trình rà soát và phê duyệt của con người.</p></div><button onClick={()=>authenticated ? setMessage('Đã lưu cấu hình chu kỳ: '+cycle+'.') : onRequireLogin()} className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Lưu cấu hình</button></section></div>
    <section className="overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="flex items-center justify-between border-b p-5"><div><h3 className="font-semibold">Duyệt đề xuất điều chỉnh lương</h3><p className="mt-1 text-xs text-slate-500">Không có thay đổi nào được áp dụng tự động.</p></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs text-amber-800">{authenticated ? suggestions.length : '—'} chờ duyệt</span></div><div className="divide-y">{suggestions.map(([id,name,team,change,reason])=><div key={id} className="flex flex-wrap items-center justify-between gap-4 p-5"><div><b>{authenticated ? name : 'Nhân viên ẩn danh'}</b><p className="mt-1 text-xs text-slate-500">{authenticated ? `${team} · ${reason}` : 'Đăng nhập HR để xem nội dung đề xuất.'}</p></div><div className="flex items-center gap-4"><b className="text-emerald-700">{authenticated ? change : masked}<small className="block text-right font-normal text-slate-400">gợi ý AI</small></b><button onClick={()=>finish(id,'Đã từ chối')} className="rounded-lg border px-3 py-2 text-xs">Từ chối</button><button onClick={()=>finish(id,'Đã phê duyệt')} className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-xs text-white"><Check size={14}/>Phê duyệt</button></div></div>)}{!suggestions.length&&<p className="p-6 text-center text-sm text-slate-500">Không còn đề xuất chờ xử lý.</p>}</div></section>
  </div>;
}

const roleLabels: Record<Role,string> = { employee:'Nhân viên', manager:'Quản lý', hr:'HR / Quản trị lương' };
export default function IncomeDashboardPage() {
  const [previewRole,setPreviewRole] = useState<Role>('employee');
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const session = useAuthStore();
  const authenticated = Boolean(session.isAuthenticated && session.user);
  const activeRole = authenticated && session.user ? session.user.role as Role : previewRole;
  const displayedRole = roleLabels[activeRole] ?? 'Người dùng';
  const content = activeRole === 'employee'
    ? <Employee />
    : activeRole === 'manager'
      ? <Manager isManager={session.user?.role === 'manager'} onRequireLogin={() => setLoginModalOpen(true)} />
      : <HrAdmin isHr={session.user?.role === 'hr'} onRequireLogin={() => setLoginModalOpen(true)} />;

  return <div className="space-y-7">
    {!authenticated ? <>
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border bg-white p-4 shadow-sm">
        <Link to="/" className="flex items-center gap-3"><span className="rounded-xl bg-indigo-600 p-2.5 text-white"><BrainCircuit size={21} /></span><span><b className="block text-sm">AI CompHub</b><small className="text-slate-500">Compensation intelligence</small></span></Link>
        <div className="flex items-center gap-2"><a href={API_DOCS_URL} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-2 text-xs font-semibold text-slate-700">Backend API / Docs</a><Link to="/login" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">Đăng nhập</Link></div>
      </header>
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm font-medium text-amber-950">Chế độ xem thử · Số liệu hiển thị là dữ liệu minh họa. Đăng nhập để truy cập đúng menu và dữ liệu theo vai trò.</div>
      <nav aria-label="Xem thử theo vai trò" className="flex w-fit max-w-full gap-1 overflow-x-auto rounded-2xl border bg-white p-1.5 shadow-sm">{([['employee','Nhân viên'],['manager','Quản lý'],['hr','HR / Quản trị lương']] as [Role,string][]).map(([id,label])=><button key={id} aria-current={previewRole===id?'page':undefined} onClick={()=>setPreviewRole(id)} className={'whitespace-nowrap rounded-xl px-4 py-2.5 text-sm font-semibold '+(previewRole===id?'bg-slate-900 text-white':'text-slate-600 hover:bg-slate-50')}>{label}</button>)}</nav>
      <nav aria-label="Phân hệ nhân sự" className="flex flex-wrap gap-2">{[['/timekeeping','Chấm công'],['/leave','Nghỉ phép & OT'],['/contracts','Hợp đồng'],['/benefits','Phúc lợi'],['/payroll','Bảng lương']].map(([to,label]) => <Link key={to} to={to} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:border-indigo-300 hover:text-indigo-700">{label}</Link>)}</nav>
    </> : <section className="rounded-2xl border border-indigo-100 bg-indigo-50 p-5"><p className="text-xs font-bold uppercase tracking-widest text-indigo-600">Không gian làm việc</p><h1 className="mt-1 text-2xl font-bold text-slate-950">{displayedRole}</h1><p className="mt-1 text-sm text-slate-600">Menu và dữ liệu bên dưới được xác định từ vai trò tài khoản do backend xác thực.</p></section>}
    {content}
    {!authenticated && <footer className="flex flex-wrap justify-between gap-2 border-t pt-5 text-xs text-slate-400"><span>AI CompHub · Thu nhập công bằng, quyết định minh bạch</span><span className="inline-flex items-center gap-1"><ShieldCheck size={13} /> Quyết định cuối cùng thuộc về con người</span></footer>}
    {loginModalOpen && <LoginRequiredModal onClose={() => setLoginModalOpen(false)} />}
  </div>;
}

