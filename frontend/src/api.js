const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const USE_API = String(import.meta.env.VITE_USE_API || 'false').toLowerCase() === 'true';

export async function apiRequest(path, { method = 'GET', body, token } = {}) {
  if (!USE_API) throw new Error('Demo mode is enabled. Configure VITE_USE_API=true to connect to FastAPI.');
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {})
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}
export const apiConfig = { API_BASE, USE_API };
