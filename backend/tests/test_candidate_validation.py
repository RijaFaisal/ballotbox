import pytest
from pydantic import ValidationError

from app.schemas.candidate import CandidateCreate, normalize_cnic


def test_name_is_required():
    with pytest.raises(ValidationError):
        CandidateCreate(product_id=1, name="   ", email="a@example.com")


def test_at_least_one_of_email_or_cnic_is_required():
    with pytest.raises(ValidationError):
        CandidateCreate(product_id=1, name="Alice")


def test_email_only_is_valid():
    candidate = CandidateCreate(product_id=1, name="Alice", email="alice@example.com")
    assert candidate.email == "alice@example.com"
    assert candidate.cnic is None


def test_cnic_only_is_valid():
    candidate = CandidateCreate(product_id=1, name="Alice", cnic="12345-1234567-1")
    assert candidate.cnic == "1234512345671"
    assert candidate.email is None


def test_both_email_and_cnic_are_allowed():
    candidate = CandidateCreate(
        product_id=1, name="Alice", email="alice@example.com", cnic="12345-1234567-1"
    )
    assert candidate.email == "alice@example.com"
    assert candidate.cnic == "1234512345671"


def test_cnic_is_normalized_to_digits_only():
    assert normalize_cnic("12345-1234567-1") == "1234512345671"
    assert normalize_cnic("1234512345671") == "1234512345671"


def test_invalid_cnic_is_rejected():
    with pytest.raises(ValidationError):
        CandidateCreate(product_id=1, name="Alice", cnic="not-a-cnic")
