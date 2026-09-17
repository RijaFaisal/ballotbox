"""products and candidates

Restructures BallotBox from a single global entry pool into a
product-based ballot system: admin-created products, customer-entered
candidates scoped to a product, and draws that run independently per
product.

This is a breaking schema change. It intentionally drops the old
entries/draws/winners tables rather than migrating their data forward --
confirmed acceptable, no production data needs to be preserved. Both the
local and production (Railway) databases must run `alembic upgrade head`
before the app will work again.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("winners")
    op.drop_table("draws")
    op.drop_table("entries")

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Case-insensitive uniqueness on product name -- a functional index,
    # since it isn't expressible as a plain UniqueConstraint.
    op.execute("CREATE UNIQUE INDEX uq_products_name_lower ON products (lower(name))")

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("cnic", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_candidates_product_id", "candidates", ["product_id"])
    # Dedup safety net matching the service-level rule (CNIC if provided,
    # else email), scoped per product and enforced at the database level
    # in case of a race between two concurrent submissions.
    op.execute(
        "CREATE UNIQUE INDEX uq_candidates_product_cnic "
        "ON candidates (product_id, cnic) WHERE cnic IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_candidates_product_email "
        "ON candidates (product_id, lower(email)) WHERE email IS NOT NULL"
    )

    op.create_table(
        "draws",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("seed", sa.String(length=128), nullable=False),
        sa.Column("drawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.CheckConstraint("status IN ('pending', 'completed', 'failed')", name="ck_draws_status"),
    )
    op.create_index("ix_draws_product_id", "draws", ["product_id"])

    op.create_table(
        "winners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "draw_id", sa.Integer(), sa.ForeignKey("draws.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "candidate_id",
            sa.Integer(),
            sa.ForeignKey("candidates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("draw_id", "candidate_id", name="uq_winners_draw_candidate"),
        sa.UniqueConstraint("draw_id", "position", name="uq_winners_draw_position"),
    )
    op.create_index("ix_winners_draw_id", "winners", ["draw_id"])
    op.create_index("ix_winners_candidate_id", "winners", ["candidate_id"])


def downgrade() -> None:
    op.drop_table("winners")
    op.drop_table("draws")
    op.execute("DROP INDEX IF EXISTS uq_candidates_product_email")
    op.execute("DROP INDEX IF EXISTS uq_candidates_product_cnic")
    op.drop_table("candidates")
    op.execute("DROP INDEX IF EXISTS uq_products_name_lower")
    op.drop_table("products")

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
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.CheckConstraint("status IN ('pending', 'completed', 'failed')", name="ck_draws_status"),
    )

    op.create_table(
        "winners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "draw_id", sa.Integer(), sa.ForeignKey("draws.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "entry_id", sa.Integer(), sa.ForeignKey("entries.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("draw_id", "entry_id", name="uq_winners_draw_entry"),
        sa.UniqueConstraint("draw_id", "position", name="uq_winners_draw_position"),
    )
    op.create_index("ix_winners_draw_id", "winners", ["draw_id"])
    op.create_index("ix_winners_entry_id", "winners", ["entry_id"])
