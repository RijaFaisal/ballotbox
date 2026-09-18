"""per-product open/close, drop global ballot_settings

Replaces the single global "is the ballot open" switch with a per-product
one: an admin can close entries for one product without closing all of
them. The old global switch no longer has any callers once this lands.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.drop_table("ballot_settings")


def downgrade() -> None:
    op.create_table(
        "ballot_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.drop_column("products", "is_open")
