from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import enum

class StudentStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    graduated = "graduated"

class CredentialType(str, enum.Enum):
    card = "card"
    face = "face"
    fingerprint = "fingerprint"

class AccessResult(str, enum.Enum):
    allow = "allow"
    deny = "deny"

class GateKind(str, enum.Enum):
    student_entry = "student_entry"
    student_exit = "student_exit"
    vehicle_entry = "vehicle_entry"
    vehicle_exit = "vehicle_exit"

class Role(str, enum.Enum):
    admin = "admin"
    registrar = "registrar"
    guard = "guard"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="guard")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="active")
    inside: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_recorded: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    credentials: Mapped[list["Credential"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="student", cascade="all, delete-orphan")

class Credential(Base):
    __tablename__ = "credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))
    # Card UID or biometric template hash — never the raw image
    template_hash: Mapped[str] = mapped_column(String(255), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student: Mapped[Student] = relationship(back_populates="credentials")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    plate: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    student: Mapped[Student | None] = relationship(back_populates="vehicles")

class Visitor(Base):
    __tablename__ = "visitors"
    id: Mapped[int] = mapped_column(primary_key=True)
    registered_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    full_name: Mapped[str] = mapped_column(String(128))
    id_number: Mapped[str] = mapped_column(String(64))
    host: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(String(255))
    pass_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Gate(Base):
    __tablename__ = "gates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(32))

class AccessEvent(Base):
    __tablename__ = "access_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    gate_id: Mapped[int] = mapped_column(ForeignKey("gates.id"), index=True)
    credential_id: Mapped[int | None] = mapped_column(ForeignKey("credentials.id"), nullable=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    visitor_id: Mapped[int | None] = mapped_column(ForeignKey("visitors.id"), nullable=True)
    result: Mapped[str] = mapped_column(String(8), index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class EnrollmentRequest(Base):
    """Tracks enrollment request IDs for idempotency + replay protection."""
    __tablename__ = "enrollment_requests"
    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
