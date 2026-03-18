import axios from 'axios';

const TOKEN_KEY = 'the_world_token';

/**
 * Pre-configured Axios instance for API communication.
 * Base URL points to the backend API prefix.
 * Automatically attaches JWT token from localStorage.
 */
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor: attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: handle auth errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl: string = error.config?.url ?? '';
      if (!requestUrl.startsWith('/auth/')) {
        localStorage.removeItem(TOKEN_KEY);
        // Redirect to home if not already there
        if (window.location.pathname !== '/') {
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  },
);

/** Helper to set the auth token in localStorage */
export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Helper to remove the auth token from localStorage */
export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/** Helper to retrieve the current auth token */
export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export default apiClient;
