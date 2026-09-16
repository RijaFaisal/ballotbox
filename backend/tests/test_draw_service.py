from __future__ import annotations

from app.models.draw import DrawStatus
from app.models.entry import Entry
from app.repositories import draw_repository, entry_repository
from app.services.draw_service import (
    DrawAlreadyCompletedError,
    NotEnoughEntriesError,
    create_pending_draw,
    execute_draw,
    run_draw,
    select_winners,
)

import pytest


def _make_entries(count: int) -> list[Entry]:
    return [
        Entry(id=i, name=f"Person {i}", identifier=f"person{i}@example.com")
        for i in range(1, count + 1)
    ]


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


# --- Seed replay: the non-negotiable proof of reproducibility --------------


def test_seed_replay_produces_identical_winners_and_positions():
    entries = _make_entries(30)

    first = select_winners(entries, seed="a-fixed-seed", winner_count=7)
    second = select_winners(entries, seed="a-fixed-seed", winner_count=7)

    assert [entry.id for entry in first] == [entry.id for entry in second]


def test_different_seeds_produce_different_winner_sets():
    entries = _make_entries(50)

    results = {
        tuple(entry.id for entry in select_winners(entries, seed=f"seed-{i}", winner_count=5))
        for i in range(10)
    }

    assert len(results) > 1


# --- DB-backed behavior ------------------------------------------------------


def test_completed_draw_cannot_be_re_run(db_session):
    _seed_entries(db_session, 10)

    draw = run_draw(db_session, winner_count=3)
    assert draw.status == DrawStatus.COMPLETED

    with pytest.raises(DrawAlreadyCompletedError):
        execute_draw(db_session, draw)


def test_winner_count_greater_than_pool_rejected_without_crash(db_session):
    _seed_entries(db_session, 2)

    with pytest.raises(NotEnoughEntriesError):
        run_draw(db_session, winner_count=5)

    draw = draw_repository.list_all(db_session)[0]
    assert draw.status == DrawStatus.FAILED
    assert draw.seed  # seed stays on record even though the draw failed


def test_winners_are_distinct(db_session):
    _seed_entries(db_session, 20)

    draw = run_draw(db_session, winner_count=8)
    winners = draw_repository.list_winners_for_draw(db_session, draw.id)

    entry_ids = [winner.entry_id for winner in winners]
    assert len(entry_ids) == len(set(entry_ids)) == 8


def test_seed_and_pending_status_persisted_before_any_winner_is_selected(db_session):
    _seed_entries(db_session, 5)

    draw = create_pending_draw(db_session, winner_count=3)

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
