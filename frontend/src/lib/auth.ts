/**
 * Authentication utilities for token management
 */

const ACCESS_TOKEN_KEY = 'portal_access_token';
const REFRESH_TOKEN_KEY = 'portal_refresh_token';

const ADMIN_ACCESS_TOKEN_KEY = 'smith_access_token';
const ADMIN_REFRESH_TOKEN_KEY = 'smith_refresh_token';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authStorage = {
  /**
   * Save authentication tokens
   */
  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return;

    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Clear all authentication tokens
   */
  clearTokens(): void {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
};

/**
 * Refresh the access token using the refresh token
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = authStorage.getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/api/portal/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh token is invalid or expired
      authStorage.clearTokens();
      return null;
    }

    const data = await response.json();
    authStorage.setTokens(data.access_token, data.refresh_token);

    return data.access_token;
  } catch (error) {
    console.error('Error refreshing token:', error);
    authStorage.clearTokens();
    return null;
  }
}

/**
 * Make an authenticated API request
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  let token = authStorage.getAccessToken();

  // First attempt
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': token ? `Bearer ${token}` : '',
    },
  });

  // If unauthorized, try to refresh token and retry
  if (response.status === 401) {
    token = await refreshAccessToken();

    if (token) {
      // Retry with new token
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
        },
      });
    } else {
      // Redirect to login if refresh failed
      if (typeof window !== 'undefined') {
        window.location.href = '/portal/login';
      }
    }
  }

  return response;
}

// ============================================
// Admin (Sistema Interno) Auth
// ============================================

export const adminAuth = {
  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(ADMIN_ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(ADMIN_REFRESH_TOKEN_KEY, refreshToken);
  },

  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ADMIN_ACCESS_TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ADMIN_REFRESH_TOKEN_KEY);
  },

  clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(ADMIN_ACCESS_TOKEN_KEY);
    localStorage.removeItem(ADMIN_REFRESH_TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },
};

export async function refreshAdminToken(): Promise<string | null> {
  const refreshToken = adminAuth.getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${API_URL}/api/admin/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      adminAuth.clearTokens();
      return null;
    }

    const data = await response.json();
    adminAuth.setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    adminAuth.clearTokens();
    return null;
  }
}

export async function adminFetch(url: string, options: RequestInit = {}): Promise<Response> {
  let token = adminAuth.getAccessToken();

  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': token ? `Bearer ${token}` : '',
    },
  });

  if (response.status === 401) {
    token = await refreshAdminToken();
    if (token) {
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
        },
      });
    } else if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  return response;
}
