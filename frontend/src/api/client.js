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
  // A FormData body (file uploads) must not get a manual Content-Type --
  // the browser sets one itself, including the multipart boundary.
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...options.headers },
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

// Shared by every "download this admin-only file" action (PDF, CSV): fetch
// with the admin token attached, honor the server's suggested filename, and
// trigger a browser download without navigating away from the SPA.
async function downloadAdminFile(path, fallbackFilename) {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      window.location.assign("/admin/login");
      throw new UnauthorizedError("Session expired.");
    }
    throw new Error("Could not download the file.");
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : fallbackFilename;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function login(payload) {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getDashboardSummary() {
  return adminRequest("/products/summary");
}

export function listProducts() {
  return adminRequest("/products");
}
export function getProduct(productId) {
  return adminRequest(`/products/${productId}`);
}
export function createProduct(name, closesAt) {
  return adminRequest("/products", {
    method: "POST",
    body: JSON.stringify({ name, closes_at: closesAt || null }),
  });
}
export function setProductOpen(productId, isOpen) {
  return adminRequest(`/products/${productId}/open`, {
    method: "POST",
    body: JSON.stringify({ is_open: isOpen }),
  });
}
export function setProductClosesAt(productId, closesAt) {
  return adminRequest(`/products/${productId}/closes-at`, {
    method: "POST",
    body: JSON.stringify({ closes_at: closesAt || null }),
  });
}
export function listCandidatesForProduct(productId) {
  return adminRequest(`/products/${productId}/candidates`);
}
export function deleteProduct(productId) {
  return adminRequest(`/products/${productId}`, { method: "DELETE" });
}
export function clearProductCandidates(productId) {
  return adminRequest(`/products/${productId}/candidates`, { method: "DELETE" });
}
export function bulkUploadProducts(file) {
  const formData = new FormData();
  formData.append("file", file);
  return adminRequest("/products/bulk-upload", { method: "POST", body: formData });
}
export function downloadCandidatesCsv(productId) {
  return downloadAdminFile(
    `/products/${productId}/candidates/export`,
    `candidates-${productId}.csv`
  );
}

export function getPublicProducts() {
  return request("/products/public");
}
export function submitCandidate(payload) {
  return request("/candidates", { method: "POST", body: JSON.stringify(payload) });
}

export function createDraw(productId, winnerCount) {
  return adminRequest(`/products/${productId}/draws`, {
    method: "POST",
    body: JSON.stringify({ winner_count: winnerCount }),
  });
}
export function listDrawsForProduct(productId) {
  return adminRequest(`/products/${productId}/draws`);
}
export function clearProductDraws(productId) {
  return adminRequest(`/products/${productId}/draws`, { method: "DELETE" });
}
export function downloadDrawPdf(productId, drawId) {
  return downloadAdminFile(
    `/products/${productId}/draws/${drawId}/export`,
    `draw-${drawId}.pdf`
  );
}

export function listAdmins() {
  return adminRequest("/admin/users");
}
export function listLoginEvents() {
  return adminRequest("/admin/users/login-events");
}
export function createAdminAccount(payload) {
  return adminRequest("/admin/users", { method: "POST", body: JSON.stringify(payload) });
}
export function deleteAdminAccount(adminId) {
  return adminRequest(`/admin/users/${adminId}`, { method: "DELETE" });
}

export function resetBallot(confirm) {
  return adminRequest("/admin/reset", { method: "POST", body: JSON.stringify({ confirm }) });
}
