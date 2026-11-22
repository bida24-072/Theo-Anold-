import hmac, hashlib, json, datetime
from app.config import settings

def _sign(body: bytes) -> str:
    return hmac.new(settings.enrollment_shared_secret.encode(), body, hashlib.sha256).hexdigest()

def test_enrollment_requires_signature(client):
    r = client.post("/enrollment/push", json={"request_id": "x", "sent_at": "2026-01-01T00:00:00", "items": []})
    assert r.status_code == 401

def test_enrollment_valid_and_idempotent(client):
    body = json.dumps({
        "request_id": "req-1",
        "sent_at": datetime.datetime.utcnow().isoformat(),
        "items": [{"student_no": "S200", "full_name": "New Student", "status": "active", "action": "upsert"}],
    }).encode()
    sig = _sign(body)

    r = client.post("/enrollment/push", content=body,
                    headers={"X-Signature": sig, "Content-Type": "application/json"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Replay same request_id → duplicate
    r2 = client.post("/enrollment/push", content=body,
                     headers={"X-Signature": sig, "Content-Type": "application/json"})
    assert r2.json()["status"] == "duplicate"
