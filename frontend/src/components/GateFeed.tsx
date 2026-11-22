import type { AccessEvent } from "../types";

export default function GateFeed({ events }: { events: AccessEvent[] }) {
  return (
    <div className="rounded-xl border border-slate-800 overflow-hidden">
      <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 text-sm font-medium">
        Recent events
      </div>
      <div className="max-h-[420px] overflow-y-auto divide-y divide-slate-800">
        {events.length === 0 && (
          <div className="p-4 text-slate-500 text-sm">No events yet.</div>
        )}
        {events.map(e => (
          <div key={e.id} className="px-4 py-2 flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <span className={`w-2 h-2 rounded-full ${e.result === "allow" ? "bg-emerald-500" : "bg-red-500"}`} />
              <span className="text-slate-300">Gate {e.gate_id}</span>
              <span className="text-slate-500">{e.reason}</span>
            </div>
            <span className="text-slate-500">{new Date(e.occurred_at).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
