import { useEffect, useState } from "react";
import { apiClient } from "../api";
import type { AccessEvent } from "../types";

export default function Reports() {
  const [events, setEvents] = useState<AccessEvent[]>([]);
  useEffect(() => { apiClient.events(200).then(setEvents).catch(() => {}); }, []);

  const denied = events.filter(e => e.result === "deny");
  const byHour: Record<number, number> = {};
  events.forEach(e => {
    const h = new Date(e.occurred_at).getHours();
    byHour[h] = (byHour[h] ?? 0) + 1;
  });
  const peak = Object.entries(byHour).sort((a, b) => b[1] - a[1]).slice(0, 3);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="rounded-xl border border-slate-800 p-4">
        <h2 className="font-medium mb-3">Summary (last {events.length} events)</h2>
        <ul className="space-y-1 text-sm">
          <li>Allowed: <span className="text-emerald-400">{events.length - denied.length}</span></li>
          <li>Denied: <span className="text-red-400">{denied.length}</span></li>
          <li>Peak hours: {peak.map(([h, n]) => `${h}:00 (${n})`).join(", ") || "—"}</li>
        </ul>
      </div>
      <div className="rounded-xl border border-slate-800 p-4">
        <h2 className="font-medium mb-3">Recent denials</h2>
        <ul className="space-y-1 text-sm">
          {denied.slice(0, 10).map(e => (
            <li key={e.id} className="flex justify-between">
              <span>Gate {e.gate_id} · {e.reason}</span>
              <span className="text-slate-500">{new Date(e.occurred_at).toLocaleTimeString()}</span>
            </li>
          ))}
          {denied.length === 0 && <li className="text-slate-500">No denials.</li>}
        </ul>
      </div>
    </div>
  );
}
