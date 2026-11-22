from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (
    Student, Credential, Vehicle, Visitor, Gate, AccessEvent,
    StudentStatus, GateKind,
)
from ..schemas import AccessCheckIn, AccessDecision, OverrideIn
from ..services import events, audit, cache
from ..deps import get_current_user, require_role

router = APIRouter(prefix="/access", tags=["access"])


def _resolve_credential(db: Session, body: AccessCheckIn) -> tuple[Student | None, Credential | None, str]:
    """Returns (student, credential, deny_reason). deny_reason empty if OK."""
    if body.credential_type and body.credential_token:
        cred = db.query(Credential).filter(
            Credential.type == body.credential_type,
            Credential.template_hash == body.credential_token,
        ).first()
        if not cred:
            return None, None, "credential_not_found"
        if cred.revoked_at is not None:
            return cred.student, cred, "credential_revoked"
        if cred.student.status != StudentStatus.active.value:
            return cred.student, cred, f"student_{cred.student.status}"
        return cred.student, cred, ""

    if body.student_no:
        s = db.query(Student).filter(Student.student_no == body.student_no).first()
        if not s:
            return None, None, "student_not_found"
        if s.status != StudentStatus.active.value:
            return s, None, f"student_{s.status}"
        return s, None, ""

    return None, None, "no_credential_supplied"


@router.post("/check", response_model=AccessDecision)
def check_access(body: AccessCheckIn, db: Session = Depends(get_db)):
    gate = db.get(Gate, body.gate_id)
    if not gate:
        raise HTTPException(404, "Gate not found")

    cache.set_gate_heartbeat(gate.id)

    # --- Vehicle gates ---
    if gate.kind in (GateKind.vehicle_entry.value, GateKind.vehicle_exit.value):
        if not body.plate:
            return AccessDecision(result="deny", reason="no_plate")
        plate = body.plate.upper().replace(" ", "")
        vehicle = db.query(Vehicle).filter(Vehicle.plate == plate).first()
        if not vehicle or vehicle.status != "active":
            ev = events.record_event(db, gate.id, "deny", "unregistered_vehicle")
            return AccessDecision(result="deny", reason="unregistered_vehicle", event_id=ev.id)
        if gate.kind == GateKind.vehicle_entry.value and vehicle.student and vehicle.student.inside:
            ev = events.record_event(db, gate.id, "deny", "vehicle_owner_already_inside",
                                     vehicle_id=vehicle.id)
            return AccessDecision(result="deny", reason="vehicle_owner_already_inside",
                                  event_id=ev.id)
        ev = events.record_event(db, gate.id, "allow", "registered_vehicle",
                                 vehicle_id=vehicle.id)
        return AccessDecision(result="allow", reason="registered_vehicle",
                              student_name=vehicle.student.full_name if vehicle.student else None,
                              event_id=ev.id)

    # --- Visitor pass ---
    if body.visitor_pass_code:
        visitor = db.query(Visitor).filter(Visitor.pass_code == body.visitor_pass_code).first()
        if not visitor:
            ev = events.record_event(db, gate.id, "deny", "visitor_not_found")
            return AccessDecision(result="deny", reason="visitor_not_found", event_id=ev.id)
        if visitor.valid_until < datetime.utcnow():
            ev = events.record_event(db, gate.id, "deny", "visitor_pass_expired",
                                     visitor_id=visitor.id)
            return AccessDecision(result="deny", reason="visitor_pass_expired", event_id=ev.id)
        ev = events.record_event(db, gate.id, "allow", "visitor_valid", visitor_id=visitor.id)
        return AccessDecision(result="allow", reason="visitor_valid",
                              student_name=visitor.full_name, event_id=ev.id)

    # --- Student gates ---
    student, cred, deny = _resolve_credential(db, body)
    if deny:
        ev = events.record_event(db, gate.id, "deny", deny,
                                 credential_id=cred.id if cred else None)
        return AccessDecision(result="deny", reason=deny, event_id=ev.id)

    assert student is not None

    if gate.kind == GateKind.student_entry.value:
        # Passback rule: must not already be inside
        if student.inside:
            ev = events.record_event(db, gate.id, "deny", "passback_already_inside",
                                     credential_id=cred.id if cred else None)
            return AccessDecision(result="deny", reason="passback_already_inside",
                                  student_name=student.full_name, event_id=ev.id)
        # Two-factor: if first factor was a card, require a second biometric
        if body.credential_type == "card":
            if not body.second_factor_token:
                ev = events.record_event(db, gate.id, "deny", "second_factor_missing",
                                         credential_id=cred.id if cred else None)
                return AccessDecision(result="deny", reason="second_factor_missing",
                                      student_name=student.full_name, event_id=ev.id)
            bio = db.query(Credential).filter(
                Credential.student_id == student.id,
                Credential.type.in_(["face", "fingerprint"]),
                Credential.template_hash == body.second_factor_token,
                Credential.revoked_at.is_(None),
            ).first()
            if not bio:
                ev = events.record_event(db, gate.id, "deny", "second_factor_mismatch",
                                         credential_id=cred.id if cred else None)
                return AccessDecision(result="deny", reason="second_factor_mismatch",
                                      student_name=student.full_name, event_id=ev.id)

        student.inside = True
        db.add(student); db.commit()

    elif gate.kind == GateKind.student_exit.value:
        # Single factor exit, mark outside
        if not student.inside:
            # Still allow the exit event but flag it
            ev = events.record_event(db, gate.id, "allow", "exit_without_entry",
                                     credential_id=cred.id if cred else None)
            return AccessDecision(result="allow", reason="exit_without_entry",
                                  student_name=student.full_name, event_id=ev.id)
        student.inside = False
        db.add(student); db.commit()

    ev = events.record_event(db, gate.id, "allow", "ok",
                             credential_id=cred.id if cred else None)
    return AccessDecision(result="allow", reason="ok",
                          student_name=student.full_name, event_id=ev.id)


@router.get("/events", response_model=list)
def list_events(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(AccessEvent).order_by(AccessEvent.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "gate_id": r.gate_id, "result": r.result,
            "reason": r.reason, "occurred_at": r.occurred_at.isoformat(),
            "credential_id": r.credential_id, "vehicle_id": r.vehicle_id,
            "visitor_id": r.visitor_id,
        }
        for r in rows
    ]


@router.post("/override", response_model=AccessDecision)
def override_gate(body: OverrideIn, db: Session = Depends(get_db),
                  user=Depends(require_role("guard", "admin"))):
    if not body.reason.strip():
        raise HTTPException(400, "Override reason is required")
    ev = events.record_event(db, body.gate_id, "allow",
                             f"guard_override_by_{user.username}: {body.reason}",
                             credential_id=body.credential_id,
                             vehicle_id=body.vehicle_id)
    audit.log_action(db, user.id, "guard_override",
                     f"gate={body.gate_id} reason={body.reason}")
    return AccessDecision(result="allow", reason=f"override: {body.reason}", event_id=ev.id)
