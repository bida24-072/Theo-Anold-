from sqlalchemy.orm import Session
from ..models import AccessEvent, Student, Credential, Vehicle, Visitor
from . import cache
from datetime import datetime

def record_event(
    db: Session,
    gate_id: int,
    result: str,
    reason: str,
    credential_id: int | None = None,
    vehicle_id: int | None = None,
    visitor_id: int | None = None,
) -> AccessEvent:
    ev = AccessEvent(
        gate_id=gate_id,
        result=result,
        reason=reason,
        credential_id=credential_id,
        vehicle_id=vehicle_id,
        visitor_id=visitor_id,
        occurred_at=datetime.utcnow(),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    cache.publish_event({
        "type": "access_event",
        "id": ev.id,
        "gate_id": ev.gate_id,
        "result": ev.result,
        "reason": ev.reason,
        "occurred_at": ev.occurred_at.isoformat(),
    })
    return ev
