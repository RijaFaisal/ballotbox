from app.repositories import product_repository
from app.schemas.candidate import CandidateCreate
from app.services.candidate_service import DuplicateCandidateError, submit_candidate

import pytest


def _product(db_session, name: str = "Grand Prize"):
    return product_repository.create(db_session, name=name)


def test_submit_candidate_creates_a_row(db_session):
    product = _product(db_session)

    candidate = submit_candidate(
        db_session, CandidateCreate(product_id=product.id, name="Alice", email="alice@example.com")
    )

    assert candidate.id is not None
    assert candidate.product_id == product.id


def test_duplicate_cnic_within_same_product_is_rejected(db_session):
    product = _product(db_session)
    submit_candidate(
        db_session, CandidateCreate(product_id=product.id, name="Alice", cnic="12345-1234567-1")
    )

    with pytest.raises(DuplicateCandidateError):
        submit_candidate(
            db_session,
            CandidateCreate(product_id=product.id, name="Alice Again", cnic="1234512345671"),
        )


def test_duplicate_email_within_same_product_is_rejected_when_no_cnic_given(db_session):
    product = _product(db_session)
    submit_candidate(
        db_session, CandidateCreate(product_id=product.id, name="Alice", email="alice@example.com")
    )

    with pytest.raises(DuplicateCandidateError):
        submit_candidate(
            db_session,
            CandidateCreate(product_id=product.id, name="Alice Again", email="ALICE@example.com"),
        )


def test_same_cnic_in_different_products_is_not_a_duplicate(db_session):
    product_a = _product(db_session, "Product A")
    product_b = _product(db_session, "Product B")
    submit_candidate(
        db_session, CandidateCreate(product_id=product_a.id, name="Alice", cnic="12345-1234567-1")
    )

    # Winning one product never excludes a person from another.
    candidate = submit_candidate(
        db_session, CandidateCreate(product_id=product_b.id, name="Alice", cnic="12345-1234567-1")
    )

    assert candidate.product_id == product_b.id


def test_dedup_checks_cnic_when_both_fields_given(db_session):
    product = _product(db_session)
    submit_candidate(
        db_session,
        CandidateCreate(
            product_id=product.id, name="Alice", email="alice@example.com", cnic="12345-1234567-1"
        ),
    )

    # Different CNIC, same email -- CNIC takes priority for dedup, so this
    # is treated as a different person, not a duplicate.
    candidate = submit_candidate(
        db_session,
        CandidateCreate(
            product_id=product.id, name="Bob", email="alice@example.com", cnic="98765-4321098-7"
        ),
    )

    assert candidate.name == "Bob"
