from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import AccessEvent, AuditLog
from ..deps import require_role

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def summary(days: int = 7, db: Session = Depends(get_db),
            _=Depends(require_role("admin", "registrar", "guard"))):
    since = datetime.utcnow() - timedelta(days=days)
    total = db.query(func.count(AccessEvent.id)).filter(AccessEvent.occurred_at >= since).scalar() or 0
    denied = db.query(func.count(AccessEvent.id)).filter(
        AccessEvent.occurred_at >= since, AccessEvent.result == "deny").scalar() or 0

    by_reason = db.query(AccessEvent.reason, func.count(AccessEvent.id)) \
        .filter(AccessEvent.occurred_at >= since, AccessEvent.result == "deny") \
        .group_by(AccessEvent.reason).all()

    by_hour = db.query(func.extract("hour", AccessEvent.occurred_at).label("h"),
                       func.count(AccessEvent.id)) \
        .filter(AccessEvent.occurred_at >= since) \
        .group_by("h").order_by("h").all()

    overrides = db.query(func.count(AuditLog.id)) \
        .filter(AuditLog.action == "guard_override", AuditLog.created_at >= since).scalar() or 0

    return {
        "window_days": days,
        "total_events": total,
        "denied": denied,
        "overrides": overrides,
        "denial_reasons": [{"reason": r, "count": c} for r, c in by_reason],
        "hourly": [{"hour": int(h), "count": c} for h, c in by_hour],
    }
