import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import IncomeDashboardPage from '@/features/ai-income/pages/IncomeDashboardPage';
import { ROUTES } from '@/config/routes.config';
import { PayrollListPage } from '@/features/payroll/pages/PayrollListPage';
import PayrollDetailPage from '@/features/payroll/pages/PayrollDetailPage';
import MyPaySlipPage from '@/features/payroll/pages/MyPaySlipPage';
import TimekeepingPage from '@/features/timekeeping/pages/TimekeepingPage';
import LeaveManagementPage from '@/features/leave-management/pages/LeaveManagementPage';
import ContractsPage from '@/features/employees/pages/ContractsPage';
import BenefitsPage from '@/features/employees/pages/BenefitsPage';
import EmployeeAdminPage from '@/features/employees/pages/EmployeeAdminPage';
import LoginPage from '@/features/auth/pages/LoginPage';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import RoleLayout from '@/layouts/RoleLayout';
import AuthLayout from '@/layouts/AuthLayout';
import { useAuthStore } from '@/store/useAuthStore';

function HomeRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <IncomeDashboardPage /> : <Navigate to={ROUTES.login} replace />;
}

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path={ROUTES.login} element={<LoginPage />} />
        </Route>
        <Route element={<RoleLayout />}>
          <Route path={ROUTES.home} element={<HomeRoute />} />
          <Route element={<ProtectedRoute allowedRoles={['hr', 'manager']} />}>
            <Route path="/payroll" element={<PayrollListPage />} />
            <Route path="/payroll/:periodId/detail" element={<PayrollDetailPage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['hr']} />}>
            <Route path="/employees" element={<EmployeeAdminPage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['employee', 'manager', 'hr']} />}>
            <Route path="/my-pay-slip" element={<MyPaySlipPage />} />
            <Route path="/my-pay-slip/:paySlipId" element={<MyPaySlipPage />} />
            <Route path="/timekeeping" element={<TimekeepingPage />} />
            <Route path="/leave" element={<LeaveManagementPage />} />
            <Route path="/contracts" element={<ContractsPage />} />
            <Route path="/benefits" element={<BenefitsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to={ROUTES.home} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
