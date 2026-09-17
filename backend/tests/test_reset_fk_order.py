"""Regression coverage for the reset's foreign-key deletion order.

SQLite ignores ON DELETE RESTRICT / CASCADE entirely unless
`PRAGMA foreign_keys = ON` is set per-connection -- the rest of this suite's
`db_session` fixture never sets it, so a wrong deletion order there would
pass silently even though it would raise an IntegrityError against
Postgres. These tests turn foreign-key enforcement on explicitly so the
constraint is actually real, then prove: (1) the constraint is real -- a
candidate can't be deleted out from under its winner row, which is exactly
the mistake the reset must avoid; (2) the reset's actual order (winners,
then draws, then candidates, then products) works even under that real
enforcement.
"""
import pytest
from sqlalchemy import create_engine, delete, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  ensures all tables are registered on Base
from app.database import Base
from app.models.candidate import Candidate
from app.models.draw import Draw, DrawStatus
from app.models.winner import Winner
from app.repositories import candidate_repository, product_repository, reset_repository
from app.services import product_service


def _fk_enforcing_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _seed_product_candidate_draw_winner(db):
    product = product_repository.create(db, name="Grand Prize")
    candidate = candidate_repository.create(
        db, product_id=product.id, name="Alice", email="alice@example.com", cnic=None
    )
    draw = Draw(product_id=product.id, seed="seed", winner_count=1, status=DrawStatus.COMPLETED)
    db.add(draw)
    db.commit()
    db.refresh(draw)
    db.add(Winner(draw_id=draw.id, candidate_id=candidate.id, position=1))
    db.commit()
    return product, candidate, draw


def test_deleting_a_candidate_before_its_winner_is_rejected():
    db = _fk_enforcing_session()
    _product, candidate, _draw = _seed_product_candidate_draw_winner(db)

    with pytest.raises(IntegrityError):
        db.execute(delete(Candidate).where(Candidate.id == candidate.id))
        db.commit()


def test_reset_ballot_succeeds_under_real_foreign_key_enforcement():
    db = _fk_enforcing_session()
    _seed_product_candidate_draw_winner(db)

    counts = reset_repository.reset_ballot(db)

    assert counts.products_deleted == 1
    assert counts.candidates_deleted == 1
    assert counts.draws_deleted == 1
    assert counts.winners_deleted == 1


def test_delete_product_succeeds_under_real_foreign_key_enforcement():
    db = _fk_enforcing_session()
    product, _candidate, _draw = _seed_product_candidate_draw_winner(db)

    counts = product_service.delete_product(db, product)

    assert counts.candidates_deleted == 1
    assert counts.draws_deleted == 1
    assert counts.winners_deleted == 1


def test_clear_candidates_succeeds_under_real_foreign_key_enforcement():
    db = _fk_enforcing_session()
    product, _candidate, _draw = _seed_product_candidate_draw_winner(db)

    counts = product_service.clear_candidates(db, product.id)

    assert counts.candidates_deleted == 1
    assert counts.draws_deleted == 1
    assert counts.winners_deleted == 1
    # The product row itself survives -- only reset_ballot/delete_product
    # remove it.
    assert product_repository.get_by_id(db, product.id) is not None
