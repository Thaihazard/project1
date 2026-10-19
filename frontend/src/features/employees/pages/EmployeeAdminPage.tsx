import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createEmployee, deactivateEmployee, getManagedEmployees, importEmployees, restoreEmployee, updateEmployeeSalary } from '../api/employeeAdmin';
import type { NewEmployee } from '../api/employeeAdmin';

const blankForm: NewEmployee = {
  fullName: '', email: '', title: '', department: '', level: 'Mid', role: 'employee',
  baseSalary: 0, kpiScore: 80, softSkillScore: 4, yearsExperience: null, certificationCount: null, initialPassword: '',
};

function getErrorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && 'errors' in detail && Array.isArray(detail.errors)) {
    return detail.errors.join(' · ');
  }
  return 'Không thể lưu hồ sơ. Hãy kiểm tra dữ liệu và quyền HR.';
}

function downloadTemplate() {
  const csv = '\uFEFFfull_name,email,title,department,level,role,base_salary,kpi_score,soft_skill_score,years_experience,certification_count\r\nNguyen Van A,employee@example.com,Backend Engineer,Engineering,Mid,employee,20000000,80,4,5,2\r\n';
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'employee-import-template.csv';
  link.click();
  URL.revokeObjectURL(url);
}

export default function EmployeeAdminPage() {
  const [form, setForm] = useState<NewEmployee>(blankForm);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [salaryEditor, setSalaryEditor] = useState<{ id: string; value: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const employees = useQuery({ queryKey: ['employees', 'admin'], queryFn: getManagedEmployees });
  const create = useMutation({
    mutationFn: createEmployee,
    onSuccess: async (employee, submitted) => {
      setForm(blankForm);
      setError('');
      setNotice(submitted.initialPassword
        ? `Đã tạo hồ sơ ${employee.fullName}. Nhân viên có thể đăng nhập bằng email và mật khẩu AI CompHub đã thiết lập, hoặc dùng Google OAuth.`
        : `Đã tạo hồ sơ ${employee.fullName}. Nhân viên đăng nhập bằng Google OAuth với email này; chưa thiết lập mật khẩu AI CompHub.`);
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
    onError: (cause) => { setNotice(''); setError(getErrorMessage(cause)); },
  });
  const importFile = useMutation({
    mutationFn: importEmployees,
    onSuccess: async (result) => {
      setError('');
      setNotice(`Đã nhập ${result.createdCount} hồ sơ và tạo tài khoản ứng dụng tương ứng.`);
      if (fileRef.current) fileRef.current.value = '';
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
    onError: (cause) => { setNotice(''); setError(getErrorMessage(cause)); },
  });
  const saveSalary = useMutation({
    mutationFn: updateEmployeeSalary,
    onSuccess: async (employee) => {
      setSalaryEditor(null);
      setError('');
      setNotice(`Đã cập nhật lương cơ bản của ${employee.fullName}.`);
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
      await queryClient.invalidateQueries({ queryKey: ['payroll'] });
    },
    onError: (cause) => { setNotice(''); setError(getErrorMessage(cause)); },
  });
  const changeEmploymentStatus = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => active ? restoreEmployee(id) : deactivateEmployee(id),
    onSuccess: async (employee) => {
      setError('');
      setNotice(employee.isActive
        ? `Đã khôi phục hồ sơ ${employee.fullName}. Họ cần đăng nhập lại để vào hệ thống.`
        : `Đã ngừng hoạt động hồ sơ ${employee.fullName}; quyền đăng nhập đã bị thu hồi.`);
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
      await queryClient.invalidateQueries({ queryKey: ['payroll'] });
    },
    onError: (cause) => { setNotice(''); setError(getErrorMessage(cause)); },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice('');
    setError('');
    create.mutate(form);
  }

  function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setNotice('');
      setError('Hãy chọn file CSV trước khi nhập.');
      return;
    }
    setNotice('');
    setError('');
    importFile.mutate(file);
  }

  return <main className="mx-auto max-w-7xl space-y-6 p-6">
    <header>
      <h1 className="text-2xl font-bold">Nhân sự &amp; cấp tài khoản</h1>
    </header>

    {notice && <p role="status" className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</p>}
    {error && <p role="alert" className="rounded-xl bg-rose-50 p-4 text-sm text-rose-800">{error}</p>}

    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6">
        <h2 className="text-lg font-semibold">Thêm một nhân viên</h2>
        <form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="text-sm">Họ và tên<input required minLength={2} maxLength={160} value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Gmail công ty<input required type="email" maxLength={255} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Mật khẩu<input type="password" autoComplete="new-password" minLength={12} maxLength={128} value={form.initialPassword ?? ''} onChange={(e) => setForm({ ...form, initialPassword: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Chức vụ<input required maxLength={160} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Phòng ban<input required maxLength={120} value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Cấp bậc<input required maxLength={40} value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Vai trò<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as NewEmployee['role'] })} className="mt-1 w-full rounded-lg border bg-white px-3 py-2"><option value="employee">Nhân viên</option><option value="manager">Quản lý</option></select></label>
          <label className="text-sm">Lương cơ bản (triệu VNĐ/tháng)<input required type="number" min={0} max={1000} step="0.1" value={form.baseSalary / 1_000_000} onChange={(e) => setForm({ ...form, baseSalary: Math.round(Number(e.target.value) * 1_000_000) })} className="mt-1 w-full rounded-lg border px-3 py-2" /><small className="mt-1 block text-xs text-slate-500">Ví dụ nhập 20 tương ứng 20.000.000 ₫.</small></label>
          <label className="text-sm">KPI hiện tại<input type="number" min={0} max={150} step="0.1" value={form.kpiScore} onChange={(e) => setForm({ ...form, kpiScore: Number(e.target.value) })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Điểm năng lực<input type="number" min={0} max={5} step="0.1" value={form.softSkillScore} onChange={(e) => setForm({ ...form, softSkillScore: Number(e.target.value) })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Số năm kinh nghiệm<input type="number" min={0} max={60} step="0.5" value={form.yearsExperience ?? ''} onChange={(e) => setForm({ ...form, yearsExperience: e.target.value === '' ? null : Number(e.target.value) })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <label className="text-sm">Số chứng chỉ<input type="number" min={0} max={100} step="1" value={form.certificationCount ?? ''} onChange={(e) => setForm({ ...form, certificationCount: e.target.value === '' ? null : Number(e.target.value) })} className="mt-1 w-full rounded-lg border px-3 py-2" /></label>
          <button disabled={create.isPending} className="self-end rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{create.isPending ? 'Đang tạo…' : 'Tạo hồ sơ & tài khoản'}</button>
        </form>
      </section>

      <section className="rounded-2xl border bg-white p-6">
        <h2 className="text-lg font-semibold">Nhập hàng loạt bằng CSV</h2>
        <p className="mt-2 text-sm text-slate-600">Tải mẫu, điền hồ sơ rồi nhập file CSV UTF-8. Chỉ lưu khi tất cả dòng hợp lệ; giới hạn 500 nhân viên mỗi file.</p>
        <button type="button" onClick={downloadTemplate} className="mt-4 rounded-lg border px-4 py-2 text-sm font-semibold text-indigo-700">Tải file CSV mẫu</button>
        <form onSubmit={upload} className="mt-5 space-y-3">
          <input ref={fileRef} type="file" accept=".csv,text/csv" className="block w-full rounded-lg border p-3 text-sm" />
          <button disabled={importFile.isPending} className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{importFile.isPending ? 'Đang nhập…' : 'Nhập hồ sơ CSV'}</button>
        </form>
      </section>
    </div>

    <section className="overflow-hidden rounded-2xl border bg-white">
      <h2 className="border-b p-5 font-semibold">Danh sách nhân sự</h2>
      {employees.isError && <p role="alert" className="p-5 text-sm text-rose-700">Không tải được danh sách. Hãy kiểm tra backend và quyền HR.</p>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-slate-50 text-slate-500"><tr>{['Mã NV', 'Nhân viên / Gmail', 'Chức vụ', 'Phòng ban', 'Vai trò', 'Lương cơ bản', 'Trạng thái', 'Thao tác'].map((heading) => <th key={heading} className="p-4">{heading}</th>)}</tr></thead>
          <tbody className="divide-y">{(employees.data ?? []).map((employee) => <tr key={employee.id}>
            <td className="p-4">{employee.id}</td><td className="p-4"><b>{employee.fullName}</b><small className="block text-slate-500">{employee.email || 'Chưa liên kết Gmail'}</small></td>
            <td className="p-4">{employee.title}</td><td className="p-4">{employee.department}</td><td className="p-4">{employee.role === 'manager' ? 'Quản lý' : 'Nhân viên'}</td>
            <td className="p-4">{new Intl.NumberFormat('vi-VN').format(employee.baseSalary)} ₫</td>
            <td className="p-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${employee.isActive ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{employee.isActive ? 'Đang làm việc' : 'Đã nghỉ'}</span></td>
            <td className="space-x-3 whitespace-nowrap p-4">{salaryEditor?.id === employee.id ? <span className="inline-flex items-center gap-2"><input aria-label={`Lương triệu đồng của ${employee.fullName}`} type="number" min={0} max={1000} step="0.1" value={salaryEditor.value} onChange={(e) => setSalaryEditor({ ...salaryEditor, value: e.target.value })} className="w-24 rounded border px-2 py-1" /><button disabled={saveSalary.isPending || salaryEditor.value === ''} onClick={() => saveSalary.mutate({ id: employee.id, baseSalary: Math.round(Number(salaryEditor.value) * 1_000_000) })} className="text-indigo-700 disabled:opacity-50">Lưu lương</button><button onClick={() => setSalaryEditor(null)} className="text-slate-500">Hủy</button></span> : <button onClick={() => setSalaryEditor({ id: employee.id, value: String(employee.baseSalary / 1_000_000) })} className="text-indigo-700 hover:underline">Sửa lương</button>}
              {employee.isActive ? <button disabled={changeEmploymentStatus.isPending} onClick={() => { if (window.confirm(`Ngừng hoạt động hồ sơ ${employee.fullName}? Quyền đăng nhập sẽ bị thu hồi; phiếu lương và lịch sử vẫn được lưu.`)) changeEmploymentStatus.mutate({ id: employee.id, active: false }); }} className="text-rose-700 hover:underline disabled:opacity-50">Xóa nhân viên</button> : <button disabled={changeEmploymentStatus.isPending} onClick={() => changeEmploymentStatus.mutate({ id: employee.id, active: true })} className="text-emerald-700 hover:underline disabled:opacity-50">Khôi phục</button>}</td>
          </tr>)}</tbody>
        </table>
      </div>
      {employees.isLoading && <p className="p-6 text-center text-sm text-slate-500">Đang tải nhân sự…</p>}
      {!employees.isLoading && !employees.isError && !employees.data?.length && <p className="p-6 text-center text-sm text-slate-500">Chưa có hồ sơ nhân viên.</p>}
    </section>
  </main>;
}
