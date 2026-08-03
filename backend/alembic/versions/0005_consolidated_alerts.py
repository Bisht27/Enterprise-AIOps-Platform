"""Add Monitoring.logged_in_user/running_processes and Alert.last_notified_at

Revision ID: 0005_consolidated_alerts
Revises: 0004_audit_and_extras
Create Date: 2026-08-03

Supports the consolidated, state-transition-based alert notification
system in app/api/v1/monitoring/service.py:

  - Monitoring.logged_in_user / running_processes: extra context the
    agent attaches to each heartbeat so the consolidated alert
    template can show "who was logged in" / process count without a
    separate lookup. Nullable so older agents keep working unchanged.

  - Alert.last_notified_at: when this specific alert last went out in
    a consolidated notification. Used to (a) know an alert is brand
    new vs. already-notified, and (b) throttle "still active"
    reminders to once every 24h per alert, instead of once per every
    monitoring cycle.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_consolidated_alerts"
down_revision: Union[str, None] = "0004_audit_and_extras"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("monitoring", sa.Column("logged_in_user", sa.String(length=150), nullable=True))
    op.add_column("monitoring", sa.Column("running_processes", sa.Integer(), nullable=True))
    op.add_column("alerts", sa.Column("last_notified_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "last_notified_at")
    op.drop_column("monitoring", "running_processes")
    op.drop_column("monitoring", "logged_in_user")
