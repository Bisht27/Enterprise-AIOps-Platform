"""Add notification service tables (notifications, preferences, templates, deliveries)

Revision ID: 0002_notifications
Revises: 0001_agent_identity
Create Date: 2026-08-01

Adds the Enterprise Notification Service tables. Does not touch any
existing table -- purely additive, per the "extend, don't rewrite"
requirement.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_notifications"
down_revision: Union[str, None] = "0001_agent_identity"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), server_default="Info"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("alerts.id"), nullable=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_read", sa.Boolean, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("email_enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("whatsapp_enabled", sa.Boolean, server_default=sa.false()),
        sa.Column("in_app_enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("critical_alerts", sa.Boolean, server_default=sa.true()),
        sa.Column("warning_alerts", sa.Boolean, server_default=sa.true()),
        sa.Column("offline_alerts", sa.Boolean, server_default=sa.true()),
        sa.Column("ticket_notifications", sa.Boolean, server_default=sa.true()),
        sa.Column("maintenance_alerts", sa.Boolean, server_default=sa.true()),
        sa.Column("security_alerts", sa.Boolean, server_default=sa.true()),
        sa.Column("daily_summary", sa.Boolean, server_default=sa.false()),
        sa.Column("weekly_summary", sa.Boolean, server_default=sa.false()),
        sa.Column("whatsapp_number", sa.String(20), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "notification_templates",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("body_template", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "notification_id",
            sa.Integer,
            sa.ForeignKey("notifications.id"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(150), nullable=False),
        sa.Column("status", sa.String(20), server_default="Pending"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("response", sa.Text, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("notification_templates")
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
