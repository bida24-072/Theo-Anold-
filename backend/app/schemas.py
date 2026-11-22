from datetime import datetime
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

class LoginIn(BaseModel):
    username: str
    password: str

# --- Enrollment ---
class EnrollmentItem(BaseModel):
    student_no: str
    full_name: str
    status: str = "active"
    action: str = Field(default="upsert", pattern="^(upsert|revoke)$")

class EnrollmentPush(BaseModel):
    request_id: str
    sent_at: datetime
    items: list[EnrollmentItem]

# --- Access ---
class AccessCheckIn(BaseModel):
    gate_id: int
    credential_type: str | None = None       # card | face | fingerprint
    credential_token: str | None = None      # card UID / face template hash / fingerprint hash
    student_no: str | None = None            # optional fallback lookup
    second_factor_token: str | None = None   # second factor for student entry
    plate: str | None = None                 # for vehicle gates
    visitor_pass_code: str | None = None     # for visitor passes

class AccessDecision(BaseModel):
    result: str  # allow | deny
    reason: str
    student_name: str | None = None
    event_id: int

class AccessEventOut(BaseModel):
    id: int
    gate_id: int
    result: str
    reason: str
    occurred_at: datetime
    credential_id: int | None = None
    vehicle_id: int | None = None
    visitor_id: int | None = None
    class Config:
        from_attributes = True

# --- Visitors ---
class VisitorCreate(BaseModel):
    full_name: str
    id_number: str
    host: str
    purpose: str
    valid_minutes: int = 120

class VisitorOut(BaseModel):
    id: int
    full_name: str
    host: str
    purpose: str
    pass_code: str
    valid_until: datetime
    class Config:
        from_attributes = True

# --- Override ---
class OverrideIn(BaseModel):
    gate_id: int
    credential_id: int | None = None
    vehicle_id: int | None = None
    reason: str

# --- Credentials ---
class CredentialCreate(BaseModel):
    student_no: str
    type: str
    template_hash: str

# --- Dashboard ---
class DashboardSnapshot(BaseModel):
    recent_events: list[AccessEventOut]
    inside_count: int
    denied_today: int
    gate_health: list[dict]
