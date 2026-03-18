import { create } from 'zustand';
import apiClient, { setAuthToken, clearAuthToken } from '@/api/client';

/** User profile as returned by the auth endpoints */
interface User {
  id: string;
  username: string;
  email: string;
  avatarUrl: string | null;
  createdAt: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  error: string | null;
}

interface AuthActions {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState & AuthActions>((set, get) => ({
  // State
  user: null,
  token: localStorage.getItem('the_world_token'),
  isAuthenticated: !!localStorage.getItem('the_world_token'),
  isLoading: false,
  isInitializing: !!localStorage.getItem('the_world_token'),
  error: null,

  // Actions
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      const response = await apiClient.post<{ access_token: string; user: User }>(
        '/auth/login',
        formData,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
      );
      const { access_token, user } = response.data;
      setAuthToken(access_token);
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const raw = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
      const message = typeof raw === 'string'
        ? raw
        : Array.isArray(raw)
          ? (raw as { msg?: string }[]).map((e) => e.msg).join('; ')
          : 'Login failed. Please check your credentials.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<{ access_token: string; user: User }>(
        '/auth/register',
        { username, email, password },
      );
      const { access_token, user } = response.data;
      setAuthToken(access_token);
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const raw = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
      const message = typeof raw === 'string'
        ? raw
        : Array.isArray(raw)
          ? (raw as { msg?: string }[]).map((e) => e.msg).join('; ')
          : 'Registration failed. Please try again.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  logout: () => {
    clearAuthToken();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
  },

  loadUser: async () => {
    const { token } = get();
    if (!token) return;

    set({ isLoading: true });
    try {
      const response = await apiClient.get<User>('/auth/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false, isInitializing: false });
    } catch {
      // Only clear if the token hasn't been replaced by a concurrent login
      if (get().token === token) {
        clearAuthToken();
        set({ user: null, token: null, isAuthenticated: false, isLoading: false, isInitializing: false });
      } else {
        set({ isLoading: false, isInitializing: false });
      }
    }
  },

  clearError: () => set({ error: null }),
}));
