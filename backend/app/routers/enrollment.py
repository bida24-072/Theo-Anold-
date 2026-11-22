import hmac, hashlib, json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Student, EnrollmentRequest, StudentStatus
from ..schemas import EnrollmentPush
from ..config import settings
from ..services import audit

router = APIRouter(prefix="/enrollment", tags=["enrollment"])

def _verify_signature(body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(
        settings.enrollment_shared_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/push")
async def push_enrollment(
    request: Request,
    x_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw = await request.body()
    if not _verify_signature(raw, x_signature):
        raise HTTPException(401, "Invalid signature")

    data = EnrollmentPush.model_validate_json(raw)

    # Replay protection / idempotency
    existing = db.get(EnrollmentRequest, data.request_id)
    if existing:
        return {"status": "duplicate", "request_id": data.request_id}

    db.add(EnrollmentRequest(request_id=data.request_id, received_at=datetime.utcnow()))

    for item in data.items:
        student = db.query(Student).filter(Student.student_no == item.student_no).first()
        if not student:
            student = Student(student_no=item.student_no, full_name=item.full_name,
                              status=item.status)
            db.add(student)
        else:
            student.full_name = item.full_name
            if item.action == "revoke":
                student.status = StudentStatus.revoked.value
            else:
                student.status = item.status
            student.updated_at = datetime.utcnow()

    db.commit()
    audit.log_action(db, None, "enrollment.push",
                     f"request_id={data.request_id} items={len(data.items)}")
    return {"status": "ok", "request_id": data.request_id, "count": len(data.items)}
