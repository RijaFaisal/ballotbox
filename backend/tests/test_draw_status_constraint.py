"""Regression test for a status enum case mismatch.

SQLAlchemy's Enum type persists an enum member's NAME ("PENDING") by
default, not its `.value` ("pending"), unless `values_callable` says
otherwise. That mismatch is invisible against the plain schema
`Base.metadata.create_all()` builds elsewhere in this suite -- it has no
CHECK constraint at all -- but it makes real Postgres reject every draw
with an IntegrityError, because the migration's ck_draws_status constraint
only allows the lowercase values.

This test builds the *exact* table the migration defines, CHECK
constraint included, against SQLite (which does enforce CHECK
constraints), so a reintroduced name/value mismatch fails here too
instead of only showing up in production.
"""
from sqlalchemy import CheckConstraint, Column, DateTime, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import Session

from app.models.draw import Draw, DrawStatus


def _draws_table_matching_migration(metadata: MetaData) -> Table:
    # Mirrors alembic/versions/0001_initial.py's draws table exactly.
    return Table(
        "draws",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("seed", String(length=128), nullable=False),
        Column("drawn_at", DateTime(timezone=True), nullable=True),
        Column("winner_count", Integer, nullable=False),
        Column("status", String(length=20), nullable=False, server_default="pending"),
        CheckConstraint("status IN ('pending', 'completed', 'failed')", name="ck_draws_status"),
    )


def test_draw_status_values_satisfy_the_database_check_constraint():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    metadata = MetaData()
    _draws_table_matching_migration(metadata)
    metadata.create_all(engine)

    with Session(engine) as session:
        for status in DrawStatus:
            draw = Draw(seed="test-seed", winner_count=1, status=status)
            session.add(draw)
            session.commit()  # raises IntegrityError if the written value isn't lowercase
            session.expunge(draw)
