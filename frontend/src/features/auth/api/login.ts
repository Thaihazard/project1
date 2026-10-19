import api from '@/lib/axios';

export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: { id: string; username: string; role: string; employeeId?: string | null; permissions: string[] };
}

export async function login(username: string, password: string) {
  const { data } = await api.post<LoginResult>('/auth/login', { username, password });
  return data;
}

export async function loginWithFirebase(credential: string) {
  const { data } = await api.post<LoginResult>('/auth/firebase', { credential });
  return data;
}
