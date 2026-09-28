import { API_URL } from "../config"

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? window.sessionStorage.getItem("cloudguard_token") : null
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } })
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? "API request failed")
  return response.json()
}
