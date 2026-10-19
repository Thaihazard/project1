import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '@/lib/axios';
import { useAuthStore } from '@/store/useAuthStore';

interface AttendanceRecord { id: string; employeeId?: string; employeeName?: string | null; attendanceDate: string; checkIn: string; checkOut: string | null; status: string }
const dateTime = (value: string | null) => value ? new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—';

export default function TimekeepingPage() {
  const user = useAuthStore((state) => state.user);
  const isReviewer = user?.role === 'manager' || user?.role === 'hr';
  const client = useQueryClient();
  const records = useQuery({ queryKey: ['attendance', isReviewer ? 'team' : 'me'], queryFn: async () => (await api.get<AttendanceRecord[]>(isReviewer ? '/attendance/team' : '/attendance/me')).data });
  const checkIn = useMutation({ mutationFn: async () => (await api.post('/attendance/check-in')).data, onSuccess: () => client.invalidateQueries({ queryKey: ['attendance', 'me'] }), onError: (error: any) => { if (error.response?.status === 409) client.invalidateQueries({ queryKey: ['attendance', 'me'] }); } });
  const checkOut = useMutation({ mutationFn: async () => (await api.post('/attendance/check-out')).data, onSuccess: () => client.invalidateQueries({ queryKey: ['attendance', 'me'] }), onError: (error: any) => { if (error.response?.status === 409) client.invalidateQueries({ queryKey: ['attendance', 'me'] }); } });
  const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' });
  const todayRecord = records.data?.find((record) => record.attendanceDate === today && (!record.employeeId || record.employeeId === user?.employeeId));
  const canTrack = user?.role === 'employee';
  const apiError = records.error as { response?: { status?: number; data?: { detail?: string } } } | null;
  const loadErrorMessage = apiError?.response?.status === 401
    ? 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để xem dữ liệu chấm công.'
    : apiError?.response?.status === 403
      ? 'Tài khoản hiện tại không có quyền xem bảng chấm công này.'
      : apiError?.response?.data?.detail ?? 'Không thể tải lịch sử chấm công. Hãy kiểm tra backend và thử tải lại.';
  const checkInError = checkIn.error as { response?: { status?: number } } | null;
  const checkOutError = checkOut.error as { response?: { status?: number } } | null;
  return <main className="mx-auto max-w-5xl space-y-6 p-6"><header className="flex items-start justify-between"><div><Link to="/" className="text-sm text-indigo-700">← AI CompHub</Link><h1 className="mt-3 text-2xl font-bold">Chấm công & thời gian làm việc</h1><p className="mt-1 text-sm text-slate-500">Theo dõi giờ vào, giờ ra và lịch sử chấm công.</p></div><div className="flex items-center gap-3"><Link to="/leave" className="rounded-lg border px-3 py-2 text-sm font-semibold text-indigo-700">Nghỉ phép & OT</Link><span className="rounded-full bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-800">{user?.role}</span></div></header>
    {canTrack && <section className="rounded-2xl border bg-white p-5"><p className="text-sm text-slate-600">Hôm nay · {new Date().toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}</p><div className="mt-3 flex flex-wrap items-center gap-3"><button disabled={!!todayRecord || checkIn.isPending} onClick={() => checkIn.mutate()} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{todayRecord ? `Đã vào lúc ${dateTime(todayRecord.checkIn)}` : 'Chấm công vào'}</button><button disabled={!todayRecord || !!todayRecord.checkOut || checkOut.isPending} onClick={() => checkOut.mutate()} className="rounded-lg border px-4 py-2 text-sm font-semibold disabled:opacity-50">{todayRecord?.checkOut ? `Đã ra lúc ${dateTime(todayRecord.checkOut)}` : 'Chấm công ra'}</button></div>{checkIn.isError && !todayRecord && <p role="alert" className="mt-3 text-sm text-rose-700">Không thể ghi nhận giờ vào. Vui lòng tải lại và thử lại.</p>}{checkOut.isError && !todayRecord?.checkOut && <p role="alert" className="mt-3 text-sm text-rose-700">{checkOutError?.response?.status === 404 ? 'Backend đang chạy phiên bản cũ, chưa có API chấm công ra. Hãy khởi động lại backend rồi thử lại.' : checkOutError?.response?.status === 409 ? 'Không thể chấm công ra: có thể bạn chưa chấm công vào hoặc đã chấm công ra hôm nay.' : 'Không thể ghi nhận giờ ra. Vui lòng kiểm tra kết nối backend và thử lại.'}</p>}{checkIn.isError && todayRecord && <p role="status" className="mt-3 text-sm text-amber-700">Giờ vào đã được ghi nhận; tải lại để đồng bộ trạng thái.</p>}</section>}
    {records.isError && <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-rose-50 p-4 text-rose-700"><span>{loadErrorMessage}</span><button onClick={() => records.refetch()} className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm font-semibold">Tải lại</button></div>}
    <section className="overflow-hidden rounded-2xl border bg-white"><h2 className="border-b p-5 font-semibold">{isReviewer ? 'Bảng chấm công nhân viên' : 'Lịch sử chấm công của tôi'}</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr>{isReviewer && <th className="p-4">Nhân viên</th>}<th className="p-4">Ngày</th><th className="p-4">Giờ vào</th><th className="p-4">Giờ ra</th><th className="p-4">Trạng thái</th></tr></thead><tbody className="divide-y">{(records.data ?? []).map((record) => <tr key={record.id}>{isReviewer && <td className="p-4">{record.employeeName}<small className="block text-slate-500">{record.employeeId}</small></td>}<td className="p-4">{new Date(record.attendanceDate + 'T00:00:00+07:00').toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}</td><td className="p-4">{dateTime(record.checkIn)}</td><td className="p-4">{dateTime(record.checkOut)}</td><td className="p-4">{record.status === 'present' ? 'Có mặt' : record.status}</td></tr>)}</tbody></table></div>{!records.isLoading && !records.data?.length && <p className="p-8 text-center text-sm text-slate-500">Chưa có dữ liệu chấm công.</p>}</section>
  </main>;
}
