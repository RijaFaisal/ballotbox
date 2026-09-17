const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "ballotbox_admin_token";

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
    // localStorage may be unavailable (private mode, blocked storage) --
    // the session simply won't persist across reloads.
  }
}
export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // see setToken
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
    const error = new Error(typeof message === "string" ? message : "Request failed");
    error.status = response.status;
    throw error;
  }
  return data;
}

function adminRequest(path, options = {}) {
  const token = getToken();
  return request(path, {
    ...options,
    isAdminRequest: true,
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
}

export function login(payload) {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getBallotStatus() {
  return request("/ballot/status");
}
export function toggleBallotStatus() {
  return adminRequest("/ballot/toggle", { method: "POST" });
}

export function listProducts() {
  return adminRequest("/products");
}
export function createProduct(name) {
  return adminRequest("/products", { method: "POST", body: JSON.stringify({ name }) });
}
export function listCandidatesForProduct(productId) {
  return adminRequest(`/products/${productId}/candidates`);
}

export function resetBallot(confirm) {
  return adminRequest("/admin/reset", { method: "POST", body: JSON.stringify({ confirm }) });
}
