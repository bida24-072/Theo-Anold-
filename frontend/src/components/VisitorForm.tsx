import { FormEvent, useState } from "react";
import { apiClient } from "../api";
import type { Visitor } from "../types";

export default function VisitorForm({ onCreated }: { onCreated: (v: Visitor) => void }) {
  const [form, setForm] = useState({ full_name: "", id_number: "", host: "", purpose: "", valid_minutes: 120 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(null);
    try {
      const v = await apiClient.createVisitor(form);
      onCreated(v);
      setForm({ full_name: "", id_number: "", host: "", purpose: "", valid_minutes: 120 });
    } catch (err: any) {
      setError(err.message ?? "Failed");
    } finally { setBusy(false); }
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: k === "valid_minutes" ? Number(e.target.value) : e.target.value });

  return (
    <form onSubmit={submit} className="rounded-xl border border-slate-800 p-4 space-y-2">
      <h3 className="font-medium mb-1">Register visitor</h3>
      <input required placeholder="Full name" value={form.full_name} onChange={set("full_name")}
             className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
      <input required placeholder="ID number" value={form.id_number} onChange={set("id_number")}
             className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
      <input required placeholder="Host" value={form.host} onChange={set("host")}
             className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
      <input required placeholder="Purpose" value={form.purpose} onChange={set("purpose")}
             className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
      <input required type="number" min={5} value={form.valid_minutes} onChange={set("valid_minutes")}
             className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
      {error && <p className="text-red-400 text-xs">{error}</p>}
      <button disabled={busy}
              className="w-full py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm">
        {busy ? "Saving…" : "Issue pass"}
      </button>
    </form>
  );
}
