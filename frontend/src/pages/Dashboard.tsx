import { useEffect, useRef, useState } from "react";
import { apiClient, auth } from "../api";
import type { AccessEvent, Snapshot, Visitor } from "../types";
import GateFeed from "../components/GateFeed";
import VisitorForm from "../components/VisitorForm";
import OverrideModal from "../components/OverrideModal";

export default function Dashboard() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [events, setEvents] = useState<AccessEvent[]>([]);
  const [visitors, setVisitors] = useState<Visitor[]>([]);
  const [overrideGate, setOverrideGate] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial snapshot + poll fallback
  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [s, v] = await Promise.all([apiClient.snapshot(), apiClient.listVisitors()]);
        if (!alive) return;
        setSnap(s);
        setEvents(s.recent_events);
        setVisitors(v);
      } catch { /* ignore */ }
    };
    load();
    const t = setInterval(load, 5000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  // Live websocket
  useEffect(() => {
    if (!auth.token) return;
    const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/dashboard/ws?token=${auth.token}`;
    // In prod behind nginx this route is /api/dashboard/ws — adjust if you mount differently.
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (m) => {
      try {
        const data = JSON.parse(m.data);
        if (data.type === "access_event") {
          const ev: AccessEvent = {
            id: data.id, gate_id: data.gate_id, result: data.result, reason: data.reason,
            occurred_at: data.occurred_at, credential_id: null, vehicle_id: null, visitor_id: null,
          };
          setEvents(prev => [ev, ...prev].slice(0, 50));
        }
      } catch { /* ignore */ }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Stat label="Inside campus" value={snap?.inside_count ?? 0} />
        <Stat label="Denied (24h)" value={snap?.denied_today ?? 0} tone="red" />
        <Stat label="Gate health"
              value={`${snap?.gate_health.filter(g => g.online).length ?? 0}/${snap?.gate_health.length ?? 0}`} />
        <Stat label="Live feed" value={connected ? "Connected" : "Polling"} tone={connected ? "emerald" : "amber"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GateFeed events={events} />
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(g => (
              <button key={g} onClick={() => setOverrideGate(g)}
                      className="px-3 py-2 rounded bg-amber-700 hover:bg-amber-600 text-sm">
                Override gate {g}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <VisitorForm onCreated={v => setVisitors(prev => [v, ...prev])} />
          <div className="rounded-xl border border-slate-800 p-4">
            <h3 className="font-medium mb-2">Active visitor passes</h3>
            <ul className="space-y-2 text-sm">
              {visitors.map(v => (
                <li key={v.id} className="border border-slate-800 rounded-lg p-2">
                  <div className="font-medium">{v.full_name}</div>
                  <div className="text-slate-400">Host: {v.host} · until {new Date(v.valid_until).toLocaleString()}</div>
                  <div className="text-emerald-400 font-mono text-xs mt-1">{v.pass_code}</div>
                </li>
              ))}
              {visitors.length === 0 && <li className="text-slate-500">No visitors yet.</li>}
            </ul>
          </div>
        </div>
      </div>

      {overrideGate !== null && (
        <OverrideModal open onClose={() => setOverrideGate(null)} gateId={overrideGate} />
      )}
    </div>
  );
}

function Stat({ label, value, tone = "slate" }: { label: string; value: string | number; tone?: string }) {
  const toneCls =
    tone === "red" ? "text-red-400" :
    tone === "emerald" ? "text-emerald-400" :
    tone === "amber" ? "text-amber-400" : "text-slate-100";
  return (
    <div className="rounded-xl border border-slate-800 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold ${toneCls}`}>{value}</div>
    </div>
  );
}
