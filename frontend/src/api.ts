const TOKEN_KEY = "theo_token";
const ROLE_KEY  = "theo_role";
const NAME_KEY  = "theo_name";

export const auth = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  get role()  { return localStorage.getItem(ROLE_KEY); },
  get name()  { return localStorage.getItem(NAME_KEY); },
  set(t: string, role: string, name: string) {
    localStorage.setItem(TOKEN_KEY, t);
    localStorage.setItem(ROLE_KEY, role);
    localStorage.setItem(NAME_KEY, name);
  },
  clear() { [TOKEN_KEY, ROLE_KEY, NAME_KEY].forEach(k => localStorage.removeItem(k)); },
};

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (auth.token) headers.set("Authorization", `Bearer ${auth.token}`);
  const res = await fetch(`/api${path}`, { ...init, headers });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const apiClient = {
  login: (username: string, password: string) =>
    api<{ access_token: string; role: string; name: string }>("/auth/login", {
      method: "POST", body: JSON.stringify({ username, password }),
    }),
  snapshot: () => api<Snapshot>("/dashboard/snapshot"),
  events: (limit = 50) => api<AccessEvent[]>(`/access/events?limit=${limit}`),
  createVisitor: (v: Omit<Visitor, "id" | "pass_code" | "valid_until"> & { valid_minutes: number }) =>
    api<Visitor>("/visitors", { method: "POST", body: JSON.stringify(v) }),
  listVisitors: () => api<Visitor[]>("/visitors"),
  override: (gate_id: number, reason: string, credential_id?: number, vehicle_id?: number) =>
    api("/access/override", { method: "POST", body: JSON.stringify({ gate_id, reason, credential_id, vehicle_id }) }),
};

// Re-export for convenience
import type { Snapshot, AccessEvent, Visitor } from "./types";
