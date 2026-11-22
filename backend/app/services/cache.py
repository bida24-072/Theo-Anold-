import json
import redis
from . import config as cfg

try:
    r = redis.Redis.from_url(cfg.settings.redis_url, decode_responses=True)
    r.ping()
except Exception:
    r = None

EVENTS_CHANNEL = "theo:events"

def publish_event(payload: dict) -> None:
    if r:
        r.publish(EVENTS_CHANNEL, json.dumps(payload, default=str))

def set_gate_heartbeat(gate_id: int) -> None:
    if r:
        r.setex(f"gate:{gate_id}:heartbeat", 30, "1")

def get_gate_health(gate_ids: list[int]) -> list[dict]:
    health = []
    for gid in gate_ids:
        alive = bool(r and r.exists(f"gate:{gid}:heartbeat"))
        health.append({"gate_id": gid, "online": alive})
    return health
