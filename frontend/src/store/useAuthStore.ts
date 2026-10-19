import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  role: string;
  employeeId?: string | null;
  permissions: string[];
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  login: (user: User, token: string, refreshToken?: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  login: (user, token, refreshToken = null) => set({ isAuthenticated: true, user, token, refreshToken }),
  logout: () => set({ isAuthenticated: false, user: null, token: null, refreshToken: null }),
}));
