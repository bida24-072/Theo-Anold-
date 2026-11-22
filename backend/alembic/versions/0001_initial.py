"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="guard"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_no", sa.String(32), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("inside", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("consent_recorded", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "credentials",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), index=True, nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("template_hash", sa.String(255), index=True, nullable=False),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), index=True, nullable=True),
        sa.Column("plate", sa.String(16), unique=True, index=True, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
    )

    op.create_table(
        "visitors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("registered_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("id_number", sa.String(64), nullable=False),
        sa.Column("host", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("pass_code", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("valid_until", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "gates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
    )

    op.create_table(
        "access_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("gate_id", sa.Integer, sa.ForeignKey("gates.id"), index=True, nullable=False),
        sa.Column("credential_id", sa.Integer, sa.ForeignKey("credentials.id"), nullable=True),
        sa.Column("vehicle_id", sa.Integer, sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("visitor_id", sa.Integer, sa.ForeignKey("visitors.id"), nullable=True),
        sa.Column("result", sa.String(8), index=True, nullable=False),
        sa.Column("reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime, index=True, nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, index=True, nullable=False),
    )

    op.create_table(
        "enrollment_requests",
        sa.Column("request_id", sa.String(64), primary_key=True),
        sa.Column("received_at", sa.DateTime, nullable=False),
    )


def downgrade():
    for t in ["enrollment_requests", "audit_log", "access_events", "gates",
              "visitors", "vehicles", "credentials", "students", "users"]:
        op.drop_table(t)
