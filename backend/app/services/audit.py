from sqlalchemy.orm import Session
from ..models import AuditLog

def log_action(db: Session, actor_id: int | None, action: str, detail: str = "") -> None:
    db.add(AuditLog(actor_id=actor_id, action=action, detail=detail))
    db.commit()
