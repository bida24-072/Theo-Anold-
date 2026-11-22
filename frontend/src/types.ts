export interface AccessEvent {
  id: number;
  gate_id: number;
  result: "allow" | "deny";
  reason: string;
  occurred_at: string;
  credential_id: number | null;
  vehicle_id: number | null;
  visitor_id: number | null;
}

export interface GateHealth { gate_id: number; online: boolean; }

export interface Snapshot {
  recent_events: AccessEvent[];
  inside_count: number;
  denied_today: number;
  gate_health: GateHealth[];
}

export interface Visitor {
  id: number;
  full_name: string;
  host: string;
  purpose: string;
  pass_code: string;
  valid_until: string;
}
