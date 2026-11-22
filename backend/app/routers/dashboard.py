from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db, SessionLocal
from ..models import AccessEvent, Student, Gate
from ..schemas import DashboardSnapshot
from ..services import cache
from ..deps import get_current_user
from ..security import decode_token
import asyncio, json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/snapshot", response_model=DashboardSnapshot)
def snapshot(db: Session = Depends(get_db), _=Depends(get_current_user)):
    recent = db.query(AccessEvent).order_by(AccessEvent.id.desc()).limit(25).all()
    inside = db.query(func.count(Student.id)).filter(Student.inside == True).scalar() or 0
    since = datetime.utcnow() - timedelta(hours=24)
    denied = db.query(func.count(AccessEvent.id)).filter(
        AccessEvent.result == "deny", AccessEvent.occurred_at >= since
    ).scalar() or 0
    gate_ids = [g.id for g in db.query(Gate).all()]
    return DashboardSnapshot(
        recent_events=[{
            "id": r.id, "gate_id": r.gate_id, "result": r.result,
            "reason": r.reason, "occurred_at": r.occurred_at,
            "credential_id": r.credential_id, "vehicle_id": r.vehicle_id,
            "visitor_id": r.visitor_id,
        } for r in recent],
        inside_count=inside,
        denied_today=denied,
        gate_health=cache.get_gate_health(gate_ids),
    )

@router.websocket("/ws")
async def dashboard_ws(ws: WebSocket, token: str):
    payload = decode_token(token)
    if not payload:
        await ws.close(code=4401)
        return
    await ws.accept()
    if cache.r is None:
        await ws.send_text(json.dumps({"type": "error", "detail": "redis not available"}))
        return
    pubsub = cache.r.pubsub()
    pubsub.subscribe(cache.EVENTS_CHANNEL)
    try:
       
