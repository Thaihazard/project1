import { useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, BarChart3, BrainCircuit, Briefcase, Eye, EyeOff, Fingerprint, LockKeyhole, Sparkles, UsersRound } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { login, loginWithFirebase } from '../api/login';
import { useAuthStore } from '@/store/useAuthStore';

const firebaseAuthConfigured = Boolean(
  import.meta.env.VITE_FIREBASE_API_KEY
  && import.meta.env.VITE_FIREBASE_AUTH_DOMAIN
  && import.meta.env.VITE_FIREBASE_PROJECT_ID
  && import.meta.env.VITE_FIREBASE_APP_ID,
);

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [pendingRole, setPendingRole] = useState('');
  const setSession = useAuthStore((state) => state.login);
  const navigate = useNavigate();
  const location = useLocation();
  const requestedLocation = (location.state as { from?: { pathname?: string; search?: string; hash?: string } } | null)?.from;
  const returnTo = requestedLocation?.pathname
    ? `${requestedLocation.pathname}${requestedLocation.search ?? ''}${requestedLocation.hash ?? ''}`
    : null;

  async function authenticate(credentials: { username: string; password: string; role?: string }) {
    setError('');
    setPendingRole(credentials.role ?? 'manual');
    try {
      const session = await login(credentials.username, credentials.password);
      setSession({
        id: session.user.id,
        name: session.user.username,
        role: session.user.role,
        employeeId: session.user.employeeId,
        permissions: session.user.permissions,
      }, session.accessToken, session.refreshToken);
      navigate(returnTo ?? '/', { replace: true });
    } catch (cause: unknown) {
      const message = (cause as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(message ?? 'Đăng nhập thất bại. Hãy kiểm tra email hoặc username, mật khẩu AI CompHub, hoặc đăng nhập bằng Google.');
    } finally {
      setPendingRole('');
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void authenticate({ username, password });
  }

  async function authenticateWithGoogle() {
    setError('');
    setPendingRole('firebase');
    try {
      const { signInWithGoogle } = await import('@/lib/firebase');
      const googleResult = await signInWithGoogle();
      const idToken = await googleResult.user.getIdToken();
      const session = await loginWithFirebase(idToken);
      setSession({
        id: session.user.id,
        name: session.user.username,
        role: session.user.role,
        employeeId: session.user.employeeId,
        permissions: session.user.permissions,
      }, session.accessToken, session.refreshToken);
      navigate(returnTo ?? '/', { replace: true });
    } catch (cause: unknown) {
      const error = cause as { response?: { data?: { detail?: string } }; message?: string };
      setError(error.response?.data?.detail ?? error.message ?? 'Đăng nhập Google thất bại. Kiểm tra cấu hình Firebase và tài khoản đã được cấp quyền.');
    } finally {
      setPendingRole('');
    }
  }

  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-indigo-800 px-12 py-10 text-white lg:flex lg:flex-col xl:px-20">
        <Link to="/" className="inline-flex w-fit items-center gap-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-white">
          <span className="rounded-xl bg-white/10 p-2.5"><BrainCircuit size={25} /></span>
          <span><b className="block text-lg">AI CompHub</b><small className="text-indigo-200">Compensation intelligence</small></span>
        </Link>

        <div className="relative z-10 mt-20 max-w-xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold text-indigo-100"><Sparkles size={14} /> Nền tảng nhân sự thông minh</p>
          <h1 className="mt-5 text-4xl font-bold leading-tight xl:text-5xl">Minh bạch thu nhập.<br /><span className="text-cyan-300">Phát triển đúng tiềm năng.</span></h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-indigo-100">Một không gian kết nối chấm công, phúc lợi, lương thưởng và phân tích AI có giải thích cho từng vai trò.</p>
        </div>

        <div className="relative mt-12 flex min-h-64 flex-1 items-center justify-center">
          <div className="absolute h-64 w-64 rounded-full border border-cyan-300/20 bg-cyan-300/5" />
          <div className="absolute h-48 w-48 rounded-full border border-white/10" />
          <div className="absolute left-[18%] top-[12%] h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_20px_8px_rgba(103,232,249,0.25)]" />
          <div className="absolute right-[18%] bottom-[20%] h-2 w-2 rounded-full bg-fuchsia-300 shadow-[0_0_20px_8px_rgba(240,171,252,0.2)]" />
          <div className="relative grid h-36 w-36 place-items-center rounded-[2rem] border border-white/20 bg-white/10 shadow-2xl backdrop-blur"><BrainCircuit size={68} strokeWidth={1.2} className="text-cyan-200" /><span className="absolute -right-3 -top-3 rounded-xl bg-cyan-300 p-2 text-slate-950"><Sparkles size={19} /></span></div>
          <div className="absolute left-0 top-5 rounded-2xl border border-white/15 bg-slate-900/60 p-4 shadow-xl backdrop-blur"><div className="flex items-center gap-3"><span className="rounded-xl bg-indigo-400/15 p-2 text-indigo-200"><UsersRound size={21} /></span><span><b className="block text-sm">Đội ngũ phát triển</b><small className="text-indigo-200">Năng lực & hiệu suất</small></span></div><div className="mt-4 flex gap-1.5"><i className="h-1.5 w-12 rounded-full bg-cyan-300"/><i className="h-1.5 w-8 rounded-full bg-indigo-300"/><i className="h-1.5 w-5 rounded-full bg-white/25"/></div></div>
          <div className="absolute right-0 top-16 rounded-2xl border border-white/15 bg-slate-900/60 p-4 shadow-xl backdrop-blur"><div className="flex items-center gap-3"><span className="rounded-xl bg-emerald-400/15 p-2 text-emerald-200"><BarChart3 size={21} /></span><span><small className="text-indigo-200">Chỉ số công bằng</small><b className="block text-lg">Minh bạch</b></span></div><div className="mt-3 flex h-8 items-end gap-1"><i className="h-3 w-2 rounded-t bg-cyan-300/60"/><i className="h-5 w-2 rounded-t bg-cyan-300/75"/><i className="h-4 w-2 rounded-t bg-cyan-300/80"/><i className="h-7 w-2 rounded-t bg-cyan-300"/><i className="h-6 w-2 rounded-t bg-indigo-300"/></div></div>
          <div className="absolute bottom-2 left-[15%] rounded-2xl border border-white/15 bg-slate-900/60 p-3 shadow-xl backdrop-blur"><div className="flex items-center gap-2 text-sm"><span className="rounded-lg bg-amber-300/15 p-2 text-amber-200"><Briefcase size={18} /></span><span><b className="block">Lộ trình nghề nghiệp</b><small className="text-indigo-200">Gợi ý theo kỹ năng</small></span></div></div>
          <div className="absolute bottom-0 right-[14%] rounded-xl border border-cyan-200/20 bg-cyan-300/10 px-3 py-2 text-xs font-semibold text-cyan-100"><Fingerprint size={14} className="mr-1 inline" /> Human-in-the-loop</div>
        </div>
        <p className="relative z-10 mt-7 text-xs text-indigo-200">AI gợi ý, con người quyết định.</p>
      </section>

      <section className="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-700 hover:text-indigo-900"><ArrowLeft size={16} /> AI CompHub</Link>
          <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/70 sm:p-9">
            <div className="mb-7">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-indigo-50 text-indigo-700"><LockKeyhole size={23} /></span>
              <h2 className="mt-5 text-3xl font-bold tracking-tight text-slate-950">Đăng nhập</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Đăng nhập để mở không gian làm việc theo đúng vai trò và quyền được cấp.</p>
            </div>

            {returnTo && <p className="mb-5 rounded-xl border border-indigo-100 bg-indigo-50 p-3 text-sm text-indigo-900">Đăng nhập thành công sẽ đưa bạn trở lại trang cần mở. Menu được chọn theo vai trò của tài khoản.</p>}

            <form className="space-y-4" onSubmit={submit}>
              <label className="block text-sm font-semibold text-slate-700">Email hoặc tài khoản AI CompHub
                <input required autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Email công ty hoặc username" className="mt-1.5 w-full rounded-xl border border-slate-300 px-3.5 py-3 font-normal outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100" />
              </label>
              <label className="block text-sm font-semibold text-slate-700">Mật khẩu
                <span className="mt-1.5 flex rounded-xl border border-slate-300 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-100"><input required type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Nhập mật khẩu" className="min-w-0 flex-1 rounded-l-xl px-3.5 py-3 font-normal outline-none placeholder:text-slate-400" /><button type="button" onClick={() => setShowPassword((value) => !value)} className="rounded-r-xl px-3 text-slate-500 hover:text-indigo-700" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></span>
              </label>
              {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
              <button disabled={!!pendingRole} className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60">{pendingRole === 'manual' ? 'Đang xác thực…' : 'Đăng nhập'} <ArrowRight size={17} /></button>
            </form>

            <div className="my-6 flex items-center gap-3 text-xs text-slate-400">
              <span className="h-px flex-1 bg-slate-200" /><span>hoặc</span><span className="h-px flex-1 bg-slate-200" />
            </div>
            {firebaseAuthConfigured ? (
              <button type="button" onClick={() => void authenticateWithGoogle()} disabled={!!pendingRole} className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60">
                <span className="grid h-5 w-5 place-items-center rounded-full border border-slate-300 text-sm font-bold text-indigo-600">G</span>
                {pendingRole === 'firebase' ? 'Đang xác thực với Google…' : 'Đăng nhập bằng Google'}
              </button>
            ) : (
              <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800">Google Sign-In chưa sẵn sàng. Hãy thêm cấu hình ứng dụng Firebase vào frontend/.env và bật Google provider trong Firebase Console.</p>
            )}

          </div>
          <p className="mt-5 text-center text-xs text-slate-400">AI CompHub · Thu nhập minh bạch, quyết định có trách nhiệm</p>
        </div>
      </section>
    </div>
  );
}
