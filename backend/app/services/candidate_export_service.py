from __future__ import annotations

import csv
import io

from sqlalchemy.orm import Session

from app.repositories import candidate_repository


def candidates_csv(db: Session, product_id: int) -> str:
    """Admin-only export -- includes email/CNIC, unlike anything a
    candidate list or PDF ever exposes."""
    candidates = candidate_repository.list_by_product_ordered_by_id(db, product_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["name", "email", "cnic", "created_at"])
    for candidate in candidates:
        writer.writerow(
            [
                candidate.name,
                candidate.email or "",
                candidate.cnic or "",
                candidate.created_at.isoformat(),
            ]
        )
    return buffer.getvalue()
