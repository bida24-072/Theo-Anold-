from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, engine, Base
from .models import User, Gate, Student, Credential, Vehicle
from .security import hash_password
from .routers import auth, enrollment, access, visitors, dashboard, reports


def seed(db: Session) -> None:
    """Idempotent seed: runs on every boot, safe to call repeatedly."""
    # --- Users (one per role) ---
    demo_users = [
        ("admin",     "Alice Admin",     "admin123",     "admin"),
        ("registrar", "Rita Registrar",  "registrar123", "registrar"),
        ("guard",     "Gary Guard",      "guard123",     "guard"),
    ]
    for username, name, pw, role in demo_users:
        if not db.query(User).filter(User.username == username).first():
            db.add(User(username=username, name=name,
                        hashed_password=hash_password(pw), role=role))

    # --- Gates (matches doc: 2 student entry, 1 student exit, 1 veh entry, 1 veh exit) ---
    demo_gates = [
        ("Student Entry A", "in",  "student_entry"),
        ("Student Entry B", "in",  "student_entry"),
        ("Student Exit",    "out", "student_exit"),
        ("Vehicle Entry",   "in",  "vehicle_entry"),
        ("Vehicle Exit",    "out", "vehicle_exit"),
    ]
    for name, direction, kind in demo_gates:
        if not db.query(Gate).filter(Gate.name == name).first():
            db.add(Gate(name=name, direction=direction, kind=kind))

    # --- One demo student with a card + face credential + vehicle ---
    student = db.query(Student).filter(Student.student_no == "S001").first()
    if not student:
        student = Student(student_no="S001", full_name="Demo Student",
                          status="active", consent_recorded=True)
        db.add(student); db.flush()
        db.add(Credential(student_id=student.id, type="card",
                          template_hash="CARD-UID-001"))
        db.add(Credential(student_id=student.id, type="face",
                          template_hash="FACE-TEMPLATE-001"))
        db.add(Vehicle(student_id=student.id, plate="B123ABC", status="active"))

    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist (Alembic also runs at container start; this is a safety net)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Theo Anold Control System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(enrollment.router)
app.include_router(access.router)
app.include_router(visitors.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}
