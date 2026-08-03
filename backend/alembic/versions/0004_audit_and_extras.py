"""Add audit log, extra notification channels, asset/user extra fields

Revision ID: 0004_audit_and_extras
Revises: 0003_reports
Create Date: 2026-08-02

Purely additive:
- audit_logs (new table)
- notification_preferences: + slack/teams/sms toggles + destinations
- assets: + department, license_expiry, next_maintenance_date
- users: + last_login_ip, failed_login_count
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_audit_and_extras"
down_revision: Union[str, None] = "0003_reports"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("target", sa.String(200), nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )

    with op.batch_alter_table("notification_preferences") as batch_op:
        batch_op.add_column(sa.Column("slack_enabled", sa.Boolean, server_default=sa.false()))
        batch_op.add_column(sa.Column("teams_enabled", sa.Boolean, server_default=sa.false()))
        batch_op.add_column(sa.Column("sms_enabled", sa.Boolean, server_default=sa.false()))
        batch_op.add_column(sa.Column("slack_webhook_url", sa.String(300), nullable=True))
        batch_op.add_column(sa.Column("teams_webhook_url", sa.String(300), nullable=True))
        batch_op.add_column(sa.Column("sms_number", sa.String(20), nullable=True))

    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(sa.Column("department", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("license_expiry", sa.DateTime, nullable=True))
        batch_op.add_column(sa.Column("next_maintenance_date", sa.DateTime, nullable=True))

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("last_login_ip", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("last_login_at", sa.DateTime, nullable=True))
        batch_op.add_column(sa.Column("failed_login_count", sa.Integer, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("failed_login_count")
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("last_login_ip")

    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_column("next_maintenance_date")
        batch_op.drop_column("license_expiry")
        batch_op.drop_column("department")

    with op.batch_alter_table("notification_preferences") as batch_op:
        batch_op.drop_column("sms_number")
        batch_op.drop_column("teams_webhook_url")
        batch_op.drop_column("slack_webhook_url")
        batch_op.drop_column("sms_enabled")
        batch_op.drop_column("teams_enabled")
        batch_op.drop_column("slack_enabled")

    op.drop_table("audit_logs")
