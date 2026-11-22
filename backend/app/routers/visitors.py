import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Visitor
from ..schemas import VisitorCreate, VisitorOut
from ..deps import require_role
from ..services import audit

router = APIRouter(prefix="/visitors", tags=["visitors"])

@router.post("", response_model=VisitorOut)
def create_visitor(body: VisitorCreate, db: Session = Depends(get_db),
                   user=Depends(require_role("guard", "admin"))):
    v = Visitor(
        registered_by=user.id,
        full_name=body.full_name,
        id_number=body.id_number,
        host=body.host,
        purpose=body.purpose,
        pass_code=secrets.token_urlsafe(16),
        valid_until=datetime.utcnow() + timedelta(minutes=body.valid_minutes),
    )
    db.add(v); db.commit(); db.refresh(v)
    audit.log_action(db, user.id, "visitor_registered", f"visitor_id={v.id}")
    return v

@router.get("", response_model=list[VisitorOut])
def list_visitors(db: Session = Depends(get_db), _=Depends(require_role("guard", "admin"))):
    return db.query(Visitor).order_by(Visitor.id.desc()).limit(50).all()
