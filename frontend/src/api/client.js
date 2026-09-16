const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail;
    throw new Error(typeof message === "string" ? message : "Request failed");
  }

  return data;
}

export function submitEntry(payload) {
  return request("/entries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
