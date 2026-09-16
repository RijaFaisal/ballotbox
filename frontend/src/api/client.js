const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "ballotbox_admin_token";

// Thrown for a 401 on an admin call, after the token has already been
// cleared and a redirect to /admin/login is already in flight. Callers can
// swallow this rather than flashing an error message right before the
// browser navigates away.
export class UnauthorizedError extends Error {}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ignore storage failures (e.g. private browsing with storage disabled)
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

async function request(path, { isAdminRequest, ...options } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && isAdminRequest) {
      clearToken();
      window.location.assign("/admin/login");
      throw new UnauthorizedError("Session expired.");
    }
    const message = data?.detail;
    throw new Error(typeof message === "string" ? message : "Request failed");
  }

  return data;
}

function adminRequest(path, options = {}) {
  const token = getToken();
  return request(path, {
    ...options,
    isAdminRequest: true,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}

export function submitEntry(payload) {
  return request("/entries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getResults() {
  return request("/results");
}

export function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEntries() {
  return adminRequest("/entries");
}

export function listDraws() {
  return adminRequest("/draws");
}

export function createDraw(winnerCount) {
  return adminRequest("/draws", {
    method: "POST",
    body: JSON.stringify({ winner_count: winnerCount }),
  });
}
