"""
Edge service: runs at each gate. Keeps a local SQLite cache of allowed
credentials so the gate still works when the network/server is down.
Syncs events to the central server when connectivity returns.
"""
import os, time, sqlite3, threading, httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SERVER_URL = os.getenv("SERVER_URL", "http://backend:8000")
GATE_ID = int(os.getenv("GATE_ID", "1"))
GATE_KIND = os.getenv("GATE_KIND", "student_entry")
EDGE_API_KEY = os.getenv("EDGE_API_KEY", "edge-key-gate-1")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "5"))
DB_PATH = os.getenv("EDGE_DB", "/data/edge.sqlite")

app = FastAPI(title=f"Edge Gate {GATE_ID}")

# ---------- Local cache ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_no TEXT PRIMARY KEY, full_name TEXT, status TEXT, inside INTEGER
        );
        CREATE TABLE IF NOT EXISTS credentials (
            template_hash TEXT PRIMARY KEY, type TEXT, student_no TEXT, revoked INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS vehicles (
            plate TEXT PRIMARY KEY, status TEXT
        );
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, created_at TEXT
        );
    """)
    conn.commit(); conn.close()

init_db()

def cache_lookup(cred_type: str, token: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT c.student_no, c.revoked, s.status, s.inside, s.full_name "
        "FROM credentials c JOIN students s ON s.student_no = c.student_no "
        "WHERE c.type=? AND c.template_hash=?", (cred_type, token)
    ).fetchone()
    conn.close()
    return row

def cache_lookup_plate(plate: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT plate, status FROM vehicles WHERE plate=?", (plate,)).fetchone()
    conn.close()
    return row

def queue_event(payload: dict):
    import json
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO outbox(payload, created_at) VALUES (?, ?)",
                 (json.dumps(payload), datetime.utcnow().isoformat()))
    conn.commit(); conn.close()

# ---------- Sync loop ----------
def sync_loop():
    import json
    while True:
        try:
            # Pull fresh allow-list from server
            r = httpx.get(f"{SERVER_URL}/enrollment/push", timeout=2)  # placeholder; see note
            # Push queued events to server
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute("SELECT id, payload FROM outbox ORDER BY id LIMIT 50").fetchall()
            conn.close()
            for rid, payload in rows:
                try:
                    httpx.post(f"{SERVER_URL}/access/check", content=payload,
                               headers={"Content-Type": "application/json"}, timeout=2)
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("DELETE FROM outbox WHERE id=?", (rid,))
                    conn.commit(); conn.close()
                except Exception:
                    break  # stay offline; retry next tick
        except Exception:
            pass
        time.sleep(SYNC_INTERVAL)

threading.Thread(target=sync_loop, daemon=True).start()

# ---------- API ----------
class CheckIn(BaseModel):
    credential_type: str | None = None
    credential_token: str | None = None
    second_factor_token: str | None = None
    plate: str | None = None

@app.get("/health")
def health():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return {"gate_id": GATE_ID, "cached_students": n}

@app.post("/check")
def check(body: CheckIn):
    # Vehicle gate
    if GATE_KIND.startswith("vehicle"):
        if not body.plate:
            return {"result": "deny", "reason": "no_plate"}
        row = cache_lookup_plate(body.plate.upper().replace(" ", ""))
        if not row or row[1] != "active":
            queue_event({"gate_id": GATE_ID, "plate": body.plate})
            return {"result": "deny", "reason": "unregistered_vehicle"}
        queue_event({"gate_id": GATE_ID, "plate": body.plate})
        return {"result": "allow", "reason": "registered_vehicle"}

    # Student gates
    if not body.credential_token:
        return {"result": "deny", "reason": "no_credential"}

    row = cache_lookup(body.credential_type or "card", body.credential_token)
    if not row:
        queue_event({"gate_id": GATE_ID,
                     "credential_type": body.credential_type,
                     "credential_token": body.credential_token})
        return {"result": "deny", "reason": "credential_not_found"}

    student_no, revoked, status, inside, full_name = row
    if revoked:
        return {"result": "deny", "reason": "credential_revoked"}
    if status != "active":
        return {"result": "deny", "reason": f"student_{status}"}
    if GATE_KIND == "student_entry" and inside:
        return {"result": "deny", "reason": "passback_already_inside"}

    queue_event({"gate_id": GATE_ID,
                 "credential_type": body.credential_type,
                 "credential_token": body.credential_token})
    return {"result": "allow", "reason": "ok", "student_name": full_name}
