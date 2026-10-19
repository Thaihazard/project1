import { useQueryClient } from '@tanstack/react-query';
import { BrainCircuit, LogOut } from 'lucide-react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { API_DOCS_URL } from '@/config/env.config';
import { useAuthStore } from '@/store/useAuthStore';

type Role = 'employee' | 'manager' | 'hr';
type MenuItem = { to: string; label: string; end?: boolean };

const roleLabels: Record<Role, string> = {
  employee: 'Nhân viên',
  manager: 'Quản lý',
  hr: 'HR Admin',
};

const menus: Record<Role, MenuItem[]> = {
  employee: [
    { to: '/', label: 'Tổng quan', end: true },
    { to: '/timekeeping', label: 'Chấm công' },
    { to: '/leave', label: 'Nghỉ phép & OT' },
    { to: '/my-pay-slip', label: 'Phiếu lương của tôi' },
    { to: '/contracts', label: 'Hợp đồng của tôi' },
    { to: '/benefits', label: 'Phúc lợi' },
  ],
  manager: [
    { to: '/', label: 'Tổng quan nhóm', end: true },
    { to: '/timekeeping', label: 'Chấm công nhóm' },
    { to: '/leave', label: 'Duyệt nghỉ phép & OT' },
    { to: '/contracts', label: 'Hợp đồng nhóm' },
    { to: '/payroll', label: 'Bảng lương nhóm' },
  ],
  hr: [
    { to: '/', label: 'AI & Công bằng thu nhập', end: true },
    { to: '/employees', label: 'Nhân sự & cấp tài khoản' },
    { to: '/timekeeping', label: 'Chấm công toàn công ty' },
    { to: '/leave', label: 'Duyệt nghỉ phép & OT' },
    { to: '/contracts', label: 'Hợp đồng nhân sự' },
    { to: '/benefits', label: 'Quản lý phúc lợi' },
    { to: '/payroll', label: 'Bảng lương toàn công ty' },
  ],
};

export default function RoleLayout() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  if (!isAuthenticated || !user) return <Outlet />;

  const role = (user.role in menus ? user.role : 'employee') as Role;
  const signOut = () => {
    logout();
    queryClient.clear();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-3">
            <span className="rounded-xl bg-indigo-600 p-2.5 text-white"><BrainCircuit size={22} /></span>
            <span><b className="block text-sm">AI CompHub</b><small className="text-slate-500">Compensation intelligence</small></span>
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <a href={API_DOCS_URL} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-2 text-xs font-semibold text-slate-600 hover:border-indigo-300 hover:text-indigo-700">Backend API / Docs</a>
            <span className="rounded-full bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-900">{user.name} · {roleLabels[role]}</span>
            <button type="button" onClick={signOut} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium hover:bg-slate-50"><LogOut size={15} /> Thoát</button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:flex-row lg:gap-8 lg:py-8">
        <aside className="w-full shrink-0 lg:w-60">
          <div className="mb-3 px-3 text-xs font-bold uppercase tracking-wider text-slate-400">Không gian {roleLabels[role]}</div>
          <nav aria-label={`Menu ${roleLabels[role]}`} className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
            {menus[role].map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `shrink-0 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors duration-150 ${isActive ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-white hover:text-indigo-700'}`}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-6 hidden rounded-2xl border border-indigo-100 bg-white p-4 text-xs leading-5 text-slate-500 lg:block">
            Menu và dữ liệu hiển thị theo quyền được cấp cho tài khoản của bạn.
          </div>
        </aside>
        <div className="min-w-0 flex-1"><Outlet /></div>
      </div>
    </div>
  );
}
