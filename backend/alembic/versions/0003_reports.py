"""Add reports module tables (scheduled_reports, export_history)

Revision ID: 0003_reports
Revises: 0002_notifications
Create Date: 2026-08-02

Purely additive -- no existing table is touched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_reports"
down_revision: Union[str, None] = "0002_notifications"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "scheduled_reports",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=True),
        sa.Column("export_format", sa.String(10), server_default="pdf"),
        sa.Column("delivery_email", sa.Boolean, server_default=sa.true()),
        sa.Column("delivery_in_app", sa.Boolean, server_default=sa.false()),
        sa.Column("recipients", sa.Text, nullable=True),
        sa.Column("filters_json", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_run_at", sa.DateTime, nullable=True),
        sa.Column("next_run_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "export_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("export_format", sa.String(10), nullable=False),
        sa.Column("file_name", sa.String(200), nullable=False),
        sa.Column("filters_json", sa.Text, nullable=True),
        sa.Column("requested_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("export_history")
    op.drop_table("scheduled_reports")
