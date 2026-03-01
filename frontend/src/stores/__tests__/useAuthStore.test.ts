import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from '../useAuthStore';

vi.mock('@/api/client', () => {
  const post = vi.fn();
  const get = vi.fn();
  return {
    default: { post, get },
    setAuthToken: vi.fn(),
    clearAuthToken: vi.fn(),
  };
});

// Import mocked module
import apiClient, { setAuthToken, clearAuthToken } from '@/api/client';

const mockedPost = vi.mocked(apiClient.post);
const mockedGet = vi.mocked(apiClient.get);

const mockUser = {
  id: '123',
  username: 'testuser',
  email: 'test@test.com',
  avatarUrl: null,
  createdAt: '2025-01-01T00:00:00Z',
};

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });
  vi.clearAllMocks();
});

describe('useAuthStore', () => {
  describe('login', () => {
    it('sends URLSearchParams format and sets state on success', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { access_token: 'jwt-token', user: mockUser },
      } as never);

      await useAuthStore.getState().login('testuser', 'Password1!');

      expect(mockedPost).toHaveBeenCalledWith(
        '/auth/login',
        expect.any(URLSearchParams),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
      );

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('jwt-token');
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(setAuthToken).toHaveBeenCalledWith('jwt-token');
    });

    it('sets error on failure', async () => {
      mockedPost.mockRejectedValueOnce({
        response: { data: { detail: 'Incorrect username or password' } },
      });

      await expect(
        useAuthStore.getState().login('bad', 'wrong'),
      ).rejects.toThrow('Incorrect username or password');

      const state = useAuthStore.getState();
      expect(state.error).toBe('Incorrect username or password');
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('register', () => {
    it('sets user and token on success', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { access_token: 'new-token', user: mockUser },
      } as never);

      await useAuthStore.getState().register('testuser', 'test@test.com', 'Password1!');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('new-token');
      expect(state.isAuthenticated).toBe(true);
      expect(setAuthToken).toHaveBeenCalledWith('new-token');
    });
  });

  describe('logout', () => {
    it('clears state', () => {
      useAuthStore.setState({
        user: mockUser,
        token: 'some-token',
        isAuthenticated: true,
      });

      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(clearAuthToken).toHaveBeenCalled();
    });
  });

  describe('loadUser', () => {
    it('fetches user when token exists', async () => {
      useAuthStore.setState({ token: 'existing-token' });
      mockedGet.mockResolvedValueOnce({ data: mockUser } as never);

      await useAuthStore.getState().loadUser();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(mockedGet).toHaveBeenCalledWith('/auth/me');
    });

    it('does not request when no token', async () => {
      useAuthStore.setState({ token: null });

      await useAuthStore.getState().loadUser();

      expect(mockedGet).not.toHaveBeenCalled();
    });
  });
});
