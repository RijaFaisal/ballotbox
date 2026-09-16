"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("identifier", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("identifier", name="uq_entries_identifier"),
    )
    op.create_index("ix_entries_identifier", "entries", ["identifier"])

    op.create_table(
        "draws",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seed", sa.String(length=128), nullable=False),
        sa.Column("drawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_count", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')", name="ck_draws_status"
        ),
    )

    op.create_table(
        "winners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "draw_id",
            sa.Integer(),
            sa.ForeignKey("draws.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("entries.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("draw_id", "entry_id", name="uq_winners_draw_entry"),
        sa.UniqueConstraint("draw_id", "position", name="uq_winners_draw_position"),
    )
    op.create_index("ix_winners_draw_id", "winners", ["draw_id"])
    op.create_index("ix_winners_entry_id", "winners", ["entry_id"])

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("username", name="uq_admins_username"),
    )
    op.create_index("ix_admins_username", "admins", ["username"])


def downgrade() -> None:
    op.drop_table("admins")
    op.drop_table("winners")
    op.drop_table("draws")
    op.drop_table("entries")
