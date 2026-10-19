import axios from 'axios';
import { API_BASE_URL } from '@/config/env.config';
import { useAuthStore } from '@/store/useAuthStore';

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  const refreshToken = useAuthStore.getState().refreshToken;
  if (error.response?.status !== 401 || !original || original._retry || !refreshToken || original.url?.includes('/auth/')) {
    return Promise.reject(error);
  }
  original._retry = true;
  try {
    const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, { refreshToken });
    const session = useAuthStore.getState();
    if (session.user) session.login(session.user, data.accessToken, data.refreshToken);
    original.headers.Authorization = `Bearer ${data.accessToken}`;
    return api(original);
  } catch (refreshError) {
    useAuthStore.getState().logout();
    return Promise.reject(refreshError);
  }
});

export default api;
