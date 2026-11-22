import { FormEvent, useState } from "react";
import { apiClient } from "../api";

export default function OverrideModal({
  open, onClose, gateId, credentialId, vehicleId,
}: {
  open: boolean; onClose: () => void; gateId: number;
  credentialId?: number; vehicleId?: number;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!open) return null;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!reason.trim()) { setError("Reason is required"); return; }
    setBusy(true); setError(null);
    try {
      await apiClient.override(gateId, reason, credentialId, vehicleId);
      setReason(""); onClose();
    } catch (err: any) { setError(err.message ?? "Failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 grid place-items-center z-50">
      <form onSubmit={submit} className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-full max-w-sm">
        <h3 className="font-medium mb-3">Guard override · Gate {gateId}</h3>
        <textarea value={reason} onChange={e => setReason(e.target.value)}
                  placeholder="Reason (logged with your name)"
                  className="w-full h-24 px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm mb-3" />
        {error && <p className="text-red-400 text-xs mb-2">{error}</p>}
        <div className="flex gap-2 justify-end">
          <button type="button" onClick={onClose}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-sm">Cancel</button>
          <button disabled={busy}
                  className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-sm disabled:opacity-50">
            {busy ? "Applying…" : "Override"}
          </button>
        </div>
      </form>
    </div>
  );
}
