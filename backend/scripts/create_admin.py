"""Create a BallotBox admin account.

This is the only way an admin gets created — there is no signup endpoint.

Usage (run from the backend/ directory, with the venv active and .env
configured so DATABASE_URL points at the right database):

    python scripts/create_admin.py <username>

You'll be prompted to type and confirm the password (input is hidden).
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.repositories import admin_repository  # noqa: E402

_MIN_PASSWORD_LENGTH = 8


def create_admin(username: str, password: str) -> None:
    username = username.strip().lower()
    db = SessionLocal()
    try:
        if admin_repository.get_by_username(db, username) is not None:
            print(f"Admin '{username}' already exists.", file=sys.stderr)
            raise SystemExit(1)

        admin = Admin(username=username, password_hash=hash_password(password))
        db.add(admin)
        db.commit()
        print(f"Admin '{username}' created.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a BallotBox admin account.")
    parser.add_argument("username")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < _MIN_PASSWORD_LENGTH:
        print(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters.", file=sys.stderr)
        raise SystemExit(1)

    create_admin(args.username, password)


if __name__ == "__main__":
    main()
