import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, auth } from "../api";

export default function Login() {
  const [username, setUsername] = useState("guard1");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await apiClient.login(username, password);
      auth.set(r.access_token, r.role, r.name);
      nav("/");
    } catch (err) {
      setError("Login failed — check username/password");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center">
      <form onSubmit={submit} className="w-full max-w-sm bg-slate-900 p-6 rounded-xl border border-slate-800">
        <h2 className="text-xl font-semibold mb-4">Sign in</h2>
        <label className="block text-sm mb-1">Username</label>
        <input value={username} onChange={e => setUsername(e.target.value)}
               className="w-full mb-3 px-3 py-2 rounded bg-slate-800 border border-slate-700" />
        <label className="block text-sm mb-1">Password</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
               className="w-full mb-4 px-3 py-2 rounded bg-slate-800 border border-slate-700" />
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <button disabled={busy}
                className="w-full py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50">
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="text-xs text-slate-500 mt-4">Demo users are seeded on first boot (see README).</p>
      </form>
    </div>
  );
}
