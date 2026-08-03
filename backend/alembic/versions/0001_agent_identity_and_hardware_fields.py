"""Add agent identity (uuid/api_key) and extended hardware/cloud fields to assets

Revision ID: 0001_agent_identity
Revises:
Create Date: 2026-08-01

This is the first migration in the project -- alembic/env.py was
previously unwired (target_metadata was None and sqlalchemy.url was a
malformed/hardcoded value), so no prior migrations exist to chain from.
If your database already has these columns for some other reason, skip
this migration; otherwise run `alembic upgrade head` from `backend/`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_agent_identity"
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


NEW_COLUMNS = [
    ("agent_uuid", sa.String(length=36)),
    ("api_key", sa.String(length=64)),
    ("os_version", sa.String(length=100)),
    ("motherboard", sa.String(length=150)),
    ("bios_version", sa.String(length=100)),
    ("gpu", sa.String(length=150)),
    ("cloud_provider", sa.String(length=50)),
    ("cloud_region", sa.String(length=50)),
    ("instance_id", sa.String(length=100)),
]


def upgrade() -> None:
    """Upgrade schema."""
    for name, col_type in NEW_COLUMNS:
        op.add_column("assets", sa.Column(name, col_type, nullable=True))

    op.create_unique_constraint("uq_assets_agent_uuid", "assets", ["agent_uuid"])
    op.create_unique_constraint("uq_assets_api_key", "assets", ["api_key"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_assets_api_key", "assets", type_="unique")
    op.drop_constraint("uq_assets_agent_uuid", "assets", type_="unique")

    for name, _ in reversed(NEW_COLUMNS):
        op.drop_column("assets", name)
