"""add login_events audit table

Records every login attempt (successful or not) so "what admin logged in
when" is answerable, and so repeated failed attempts are visible too.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "admin_id",
            sa.Integer(),
            sa.ForeignKey("admins.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_login_events_admin_id", "login_events", ["admin_id"])
    op.create_index("ix_login_events_created_at", "login_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_login_events_created_at", table_name="login_events")
    op.drop_index("ix_login_events_admin_id", table_name="login_events")
    op.drop_table("login_events")
