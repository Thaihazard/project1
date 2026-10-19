import api from '@/lib/axios';

export interface ManagedEmployee {
  id: string;
  fullName: string;
  email: string | null;
  title: string;
  department: string;
  level: string;
  role: 'employee' | 'manager';
  isActive: boolean;
  baseSalary: number;
  kpiScore: number;
  softSkillScore?: number | null;
  yearsExperience?: number | null;
  certificationCount?: number | null;
}

export interface NewEmployee {
  fullName: string;
  email: string;
  title: string;
  department: string;
  level: string;
  role: 'employee' | 'manager';
  baseSalary: number;
  kpiScore: number;
  softSkillScore: number;
  yearsExperience?: number | null;
  certificationCount?: number | null;
  initialPassword?: string | null;
}

export async function getManagedEmployees() {
  const { data } = await api.get<ManagedEmployee[]>('/employees');
  return data;
}

export async function createEmployee(input: NewEmployee) {
  const { data } = await api.post<ManagedEmployee>('/employees', input);
  return data;
}

export async function updateEmployeeSalary(input: { id: string; baseSalary: number }) {
  const { data } = await api.patch<ManagedEmployee>(`/employees/${encodeURIComponent(input.id)}/salary`, {
    baseSalary: input.baseSalary,
  });
  return data;
}

export async function deactivateEmployee(id: string) {
  const { data } = await api.delete<ManagedEmployee>(`/employees/${encodeURIComponent(id)}`);
  return data;
}

export async function restoreEmployee(id: string) {
  const { data } = await api.post<ManagedEmployee>(`/employees/${encodeURIComponent(id)}/restore`);
  return data;
}

export async function importEmployees(file: File) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<{ createdCount: number; employees: ManagedEmployee[] }>('/employees/import', form);
  return data;
}
