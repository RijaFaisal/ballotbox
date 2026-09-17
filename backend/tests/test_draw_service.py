from __future__ import annotations

from app.models.candidate import Candidate
from app.models.draw import DrawStatus
from app.repositories import candidate_repository, draw_repository, product_repository
from app.services.draw_service import (
    DrawAlreadyCompletedError,
    NotEnoughEntriesError,
    create_pending_draw,
    execute_draw,
    run_draw,
    select_winners,
)

import pytest


def _make_candidates(count: int) -> list[Candidate]:
    return [
        Candidate(id=i, product_id=1, name=f"Person {i}", email=f"person{i}@example.com")
        for i in range(1, count + 1)
    ]


def _seed_product_with_candidates(db_session, count: int) -> int:
    product = product_repository.create(db_session, name="Grand Prize")
    for i in range(1, count + 1):
        candidate_repository.create(
            db_session,
            product_id=product.id,
            name=f"Person {i}",
            email=f"person{i}@example.com",
            cnic=None,
        )
    return product.id


# --- Seed replay: the non-negotiable proof of reproducibility --------------


def test_seed_replay_produces_identical_winners_and_positions():
    candidates = _make_candidates(30)

    first = select_winners(candidates, seed="a-fixed-seed", winner_count=7)
    second = select_winners(candidates, seed="a-fixed-seed", winner_count=7)

    assert [candidate.id for candidate in first] == [candidate.id for candidate in second]


def test_different_seeds_produce_different_winner_sets():
    candidates = _make_candidates(50)

    results = {
        tuple(candidate.id for candidate in select_winners(candidates, seed=f"seed-{i}", winner_count=5))
        for i in range(10)
    }

    assert len(results) > 1


# --- DB-backed behavior ------------------------------------------------------


def test_completed_draw_cannot_be_re_run(db_session):
    product_id = _seed_product_with_candidates(db_session, 10)

    draw = run_draw(db_session, product_id=product_id, winner_count=3)
    assert draw.status == DrawStatus.COMPLETED

    with pytest.raises(DrawAlreadyCompletedError):
        execute_draw(db_session, draw)


def test_winner_count_greater_than_pool_rejected_without_crash(db_session):
    product_id = _seed_product_with_candidates(db_session, 2)

    with pytest.raises(NotEnoughEntriesError):
        run_draw(db_session, product_id=product_id, winner_count=5)

    draw = draw_repository.list_all(db_session)[0]
    assert draw.status == DrawStatus.FAILED
    assert draw.seed  # seed stays on record even though the draw failed


def test_winners_are_distinct(db_session):
    product_id = _seed_product_with_candidates(db_session, 20)

    draw = run_draw(db_session, product_id=product_id, winner_count=8)
    winners = draw_repository.list_winners_for_draw(db_session, draw.id)

    candidate_ids = [winner.candidate_id for winner in winners]
    assert len(candidate_ids) == len(set(candidate_ids)) == 8


def test_a_draw_never_selects_a_candidate_from_another_product(db_session):
    product_id = _seed_product_with_candidates(db_session, 5)
    _other_product_id = _seed_product_with_candidates(db_session, 5)

    draw = run_draw(db_session, product_id=product_id, winner_count=1)
    winners = draw_repository.list_winners_for_draw(db_session, draw.id)

    assert winners[0].candidate.product_id == product_id


def test_seed_and_pending_status_persisted_before_any_winner_is_selected(db_session):
    product_id = _seed_product_with_candidates(db_session, 5)

    draw = create_pending_draw(db_session, product_id=product_id, winner_count=3)

    # Re-fetch independently to prove this was actually committed to the
    # database, not just held in the ORM session's local state.
    persisted = draw_repository.get_by_id(db_session, draw.id)
    assert persisted is not None
    assert persisted.seed == draw.seed
    assert persisted.status == DrawStatus.PENDING
    assert draw_repository.list_winners_for_draw(db_session, draw.id) == []

    completed = execute_draw(db_session, draw)

    assert completed.status == DrawStatus.COMPLETED
    assert len(draw_repository.list_winners_for_draw(db_session, draw.id)) == 3
