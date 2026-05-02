import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenResponse,
  User,
  Organization,
  OrgProfileRead,
  PaginatedResponse,
  Grant,
  Application,
  ApplicationSection,
  OrgDocument,
  Deadline,
  ApiError,
} from "@orchestragrant/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/v1";

// ─── Token storage (memory + cookie for SSR) ────────────────────────────────

let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

// ─── Core fetch wrapper ────────────────────────────────────────────────────

interface FetchOptions extends RequestInit {
  auth?: boolean;
}

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiError
  ) {
    super(body.detail ?? body.title);
    this.name = "ApiRequestError";
  }
}

async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { auth = true, ...rest } = opts;

  // Wait for auth init to complete before making authenticated requests
  if (auth && !_accessToken && _authInitPromise) {
    await _authInitPromise;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(rest.headers as Record<string, string>),
  };

  if (auth && _accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers });

  if (res.status === 401) {
    // Attempt silent token refresh
    const refreshed = await _silentRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${_accessToken}`;
      const retryRes = await fetch(`${API_BASE}${path}`, { ...rest, headers });
      if (!retryRes.ok) {
        const body = await retryRes.json().catch(() => ({}));
        throw new ApiRequestError(retryRes.status, body);
      }
      return retryRes.json() as Promise<T>;
    }
    // Refresh failed — throw so the caller can handle it
    throw new ApiRequestError(401, {
      type: "unauthorized",
      title: "Unauthorized",
      status: 401,
      detail: "Session expired",
    });
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({
      type: "error",
      title: "Error",
      status: res.status,
      detail: res.statusText,
    }));
    throw new ApiRequestError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

let _refreshPromise: Promise<boolean> | null = null;

async function _silentRefresh(): Promise<boolean> {
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = (async () => {
    try {
      const refreshToken =
        typeof localStorage !== "undefined"
          ? localStorage.getItem("og_refresh_token")
          : null;
      if (!refreshToken) return false;

      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        localStorage.removeItem("og_refresh_token");
        return false;
      }
      const data: RefreshTokenResponse & { refresh_token?: string } = await res.json();
      setAccessToken(data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("og_refresh_token", data.refresh_token);
      }
      return true;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();
  return _refreshPromise;
}

/** Call once on app mount to restore the access token from the stored refresh token. */
let _authInitPromise: Promise<void> | null = null;

export function initAuth(): Promise<void> {
  if (_authInitPromise) return _authInitPromise;
  _authInitPromise = (async () => {
    if (_accessToken) return;
    await _silentRefresh();
  })();
  return _authInitPromise;
}

// Start auth init immediately when the module loads in the browser so
// _authInitPromise is set before any component mounts and fires queries.
if (typeof window !== "undefined") {
  initAuth();
}

// ─── Auth endpoints ─────────────────────────────────────────────────────────

export const authApi = {
  login: (body: LoginRequest) =>
    apiFetch<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(body), auth: false }),

  logout: () => apiFetch<void>("/auth/logout", { method: "POST" }),

  setupMfa: () => apiFetch<{ secret: string; qr_data_uri: string }>("/auth/mfa/setup", { method: "POST" }),

  verifyMfa: (totp_code: string) =>
    apiFetch<void>("/auth/mfa/verify", { method: "POST", body: JSON.stringify({ totp_code }) }),
};

// ─── Users ──────────────────────────────────────────────────────────────────

export const usersApi = {
  getMe: () => apiFetch<User>("/users/me"),
  updateMe: (data: Partial<User>) =>
    apiFetch<User>("/users/me", { method: "PATCH", body: JSON.stringify(data) }),
  list: () => apiFetch<User[]>("/users"),
  invite: (data: { email: string; first_name: string; last_name: string; role: string }) =>
    apiFetch<User>("/users/invite", { method: "POST", body: JSON.stringify(data) }),
  deactivate: (userId: string) =>
    apiFetch<void>(`/users/${userId}/deactivate`, { method: "PATCH" }),
};

// ─── Organizations ────────────────────────────────────────────────────────────

export const orgsApi = {
  getMe: () => apiFetch<Organization>("/organizations/me"),
  update: (data: Partial<Organization>) =>
    apiFetch<Organization>("/organizations/me", { method: "PATCH", body: JSON.stringify(data) }),
  getProfile: () => apiFetch<OrgProfileRead>("/organizations/me/profile"),
  updateProfile: (data: Partial<OrgProfileRead>) =>
    apiFetch<OrgProfileRead>("/organizations/me/profile", { method: "PATCH", body: JSON.stringify(data) }),
};

type OrgProfileRead = {
  id: string;
  org_id: string;
  mission?: string;
  vision?: string;
  programs_description?: string;
  geographic_scope?: string;
  primary_artistic_focus?: string;
  performances_per_year?: number;
  audience_size?: number;
  member_musicians?: number;
  community_impact_statement?: string;
  diversity_statement?: string;
  updated_at: string;
};

// ─── Grants ────────────────────────────────────────────────────────────────

export interface GrantSearchParams {
  query?: string;
  type?: string;
  funder_type?: string;
  min_amount?: number;
  max_amount?: number;
  arts_specific?: boolean;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export const grantsApi = {
  list: (params: GrantSearchParams = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => [k, String(v)])
    ).toString();
    return apiFetch<{ items: Grant[]; total: number; page: number; page_size: number; has_more: boolean }>(
      `/grants${qs ? `?${qs}` : ""}`
    );
  },
  get: (id: string) => apiFetch<Grant>(`/grants/${id}`),
  addToWatchlist: (id: string) => apiFetch<void>(`/grants/${id}/watchlist`, { method: "POST" }),
  removeFromWatchlist: (id: string) => apiFetch<void>(`/grants/${id}/watchlist`, { method: "DELETE" }),
  getWatchlist: () => apiFetch<Grant[]>("/grants/watchlist/me"),
};

// ─── Applications ─────────────────────────────────────────────────────────────

export const applicationsApi = {
  list: (params: { stage?: string; page?: number; page_size?: number } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
    ).toString();
    return apiFetch<{ items: Application[]; total: number; page: number; page_size: number; has_more: boolean }>(
      `/applications${qs ? `?${qs}` : ""}`
    );
  },
  get: (id: string) => apiFetch<Application>(`/applications/${id}`),
  create: (data: Partial<Application>) =>
    apiFetch<Application>("/applications", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Application>) =>
    apiFetch<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => apiFetch<void>(`/applications/${id}`, { method: "DELETE" }),
  transition: (id: string, new_stage: string, note?: string) =>
    apiFetch<Application>(`/applications/${id}/stage`, {
      method: "POST",
      body: JSON.stringify({ new_stage, note }),
    }),

  // Sections
  getSections: (appId: string) => apiFetch<ApplicationSection[]>(`/applications/${appId}/sections`),
  updateSection: (appId: string, sectionId: string, data: { content?: string; status?: string }) =>
    apiFetch<ApplicationSection>(`/applications/${appId}/sections/${sectionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  lockSection: (appId: string, sectionId: string) =>
    apiFetch<ApplicationSection>(`/applications/${appId}/sections/${sectionId}/lock`, { method: "POST" }),
  unlockSection: (appId: string, sectionId: string) =>
    apiFetch<void>(`/applications/${appId}/sections/${sectionId}/lock`, { method: "DELETE" }),
  generateSection: (appId: string, sectionId: string) =>
    apiFetch<ApplicationSection>(`/applications/${appId}/sections/${sectionId}/generate`, { method: "POST" }),
};

// ─── Documents ────────────────────────────────────────────────────────────────

export const documentsApi = {
  list: (category?: string) =>
    apiFetch<OrgDocument[]>(`/documents${category ? `?category=${category}` : ""}`),
  getUploadUrl: (data: {
    file_name: string;
    mime_type: string;
    file_size_bytes: number;
    category: string;
    year?: number;
    description?: string;
  }) => apiFetch<{ upload_url: string; document_id: string; expires_in: number }>("/documents/upload-url", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  confirmUpload: (docId: string) =>
    apiFetch<void>(`/documents/${docId}/confirm`, { method: "POST" }),
  getDownloadUrl: (docId: string) =>
    apiFetch<{ download_url: string; expires_in: number }>(`/documents/${docId}/download-url`),
  delete: (docId: string) => apiFetch<void>(`/documents/${docId}`, { method: "DELETE" }),
};

// ─── Deadlines ────────────────────────────────────────────────────────────────

export const deadlinesApi = {
  list: (upcomingOnly = false) =>
    apiFetch<Deadline[]>(`/deadlines${upcomingOnly ? "?upcoming_only=true" : ""}`),
  create: (data: { title: string; deadline_at: string; type?: string; application_id?: string; grant_id?: string; notes?: string; reminder_days?: number[] }) =>
    apiFetch<Deadline>("/deadlines", { method: "POST", body: JSON.stringify(data) }),
  complete: (id: string) => apiFetch<Deadline>(`/deadlines/${id}/complete`, { method: "PATCH" }),
  delete: (id: string) => apiFetch<void>(`/deadlines/${id}`, { method: "DELETE" }),
};
