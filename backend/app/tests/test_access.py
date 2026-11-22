from app.models import Student, Credential

def _seed_student(db):
    from app.database import Base
    s = Student(student_no="S100", full_name="Test", status="active")
    db.add(s); db.flush()
    db.add(Credential(student_id=s.id, type="card", template_hash="CARD-1"))
    db.add(Credential(student_id=s.id, type="face", template_hash="FACE-1"))
    db.commit()
    return s

def test_entry_two_factor_allow(client):
    from app.tests.conftest import TestingSession
    db = TestingSession(); _seed_student(db); db.close()

    r = client.post("/access/check", json={
        "gate_id": 1, "credential_type": "card",
        "credential_token": "CARD-1", "second_factor_token": "FACE-1",
    })
    assert r.status_code == 200
    assert r.json()["result"] == "allow"

def test_entry_missing_second_factor_denied(client):
    from app.tests.conftest import TestingSession
    db = TestingSession(); _seed_student(db); db.close()

    r = client.post("/access/check", json={
        "gate_id": 1, "credential_type": "card", "credential_token": "CARD-1",
    })
    assert r.json()["result"] == "deny"
    assert r.json()["reason"] == "second_factor_missing"

def test_passback_rule(client):
    from app.tests.conftest import TestingSession
    db = TestingSession(); _seed_student(db); db.close()
    payload = {
        "gate_id": 1, "credential_type": "card",
        "credential_token": "CARD-1", "second_factor_token": "FACE-1",
    }
    first = client.post("/access/check", json=payload)
    assert first.json()["result"] == "allow"

    second = client.post("/access/check", json=payload)
    assert second.json()["result"] == "deny"
    assert second.json()["reason"] == "passback_already_inside"
