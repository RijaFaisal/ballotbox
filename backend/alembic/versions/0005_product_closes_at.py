"""add scheduled close time to products

Adds an optional closes_at deadline per product, independent of the
existing is_open manual toggle: once closes_at passes, the product is
treated as closed for entries regardless of is_open's value.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("closes_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "closes_at")
