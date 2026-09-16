# BallotBox

A small raffle/ballot system: the public enters a name and an email or
CNIC, an admin runs a seeded, reproducible random draw, and anyone can
view the winners on a public results page.

## How it works

- **Entry** — anyone submits `name` + `identifier` (email or 13-digit
  Pakistani CNIC). Duplicate identifiers are rejected. Identifiers are
  normalized (CNIC digits-only, email lowercased) so `12345-1234567-1`
  and `1234512345671` dedupe against each other.
- **Draw** — an admin picks a `winner_count` and runs a draw. The
  service generates a random seed, **persists it to the database before
  any selection happens** (the audit anchor), then seeds
  `random.Random(seed)` and samples winners from all entries sorted by
  id. Given the same seed and entry set, the selection is exactly
  reproducible. A completed draw is immutable — re-running it is
  rejected; a redo creates a brand-new draw row with a new seed, and
  both stay on record permanently.
- **Results** — the public results page shows the winners (name +
  position) and the draw date for the most recently completed draw.
  Identifiers are never exposed here or anywhere outside the admin's
  own entry list.

## Architecture

Backend is a layered FastAPI app; each slice (entries, auth, draws,
results) follows the same shape:

```
routes/       FastAPI routers — HTTP concerns and status codes only
services/     business logic (draw selection, auth, duplicate checks)
repositories/ all database access (SQLAlchemy queries)
schemas/      Pydantic v2 request/response models
models/       SQLAlchemy ORM tables
core/         security primitives (JWT, password hashing) and the
              get_current_admin auth dependency
```

Frontend is a small React + Vite app with client-side routing
(`react-router-dom`):

```
/            public entry form
/results     public results page
/admin/login admin login
/admin       admin dashboard (protected — bounces to /admin/login
             without a valid token)
```

### Data model

- `entries` — id, name, identifier (unique), created_at
- `draws` — id, seed, winner_count, status (pending/completed/failed), drawn_at
- `winners` — join table: draw_id, entry_id, position (unique per draw)
- `admins` — id, username, password_hash (bcrypt)

### Endpoints

| Method | Path           | Auth  | Notes                                            |
|--------|----------------|-------|---------------------------------------------------|
| POST   | `/entries`     | -     | Submit an entry                                    |
| GET    | `/entries`     | admin | List entries (names only, no identifiers)          |
| POST   | `/auth/login`  | -     | Returns a JWT                                      |
| GET    | `/auth/me`     | admin | Confirms the current token                         |
| POST   | `/draws`       | admin | Runs a new draw                                    |
| GET    | `/draws`       | admin | Lists past draws (seed, status, timestamps)        |
| GET    | `/draws/{id}`  | admin | One draw with its winners                          |
| GET    | `/results`     | -     | Winners of the latest completed draw               |
| GET    | `/health`      | -     | Health check                                       |

## Project layout

```
backend/
  app/                FastAPI application (see Architecture above)
  alembic/             database migrations
  scripts/create_admin.py   the only way to create an admin account
  tests/               pytest suite
  requirements.txt      runtime dependencies
  requirements-dev.txt   + pytest, httpx
frontend/
  src/                 React app
  vercel.json           SPA rewrite rule for client-side routing
```

## Local setup

### Backend

Requires Python 3.11+ and a Postgres database (SQLite works for tests only).

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # then fill in DATABASE_URL and JWT_SECRET_KEY
alembic upgrade head
python scripts/create_admin.py <username>   # prompts for a password
uvicorn app.main:app --reload
```

The API serves on `http://localhost:8000`.

**Environment variables** (`backend/.env`, see `.env.example`):

| Variable             | Required | Default                | Notes                                              |
|----------------------|----------|-------------------------|-----------------------------------------------------|
| `DATABASE_URL`       | yes      | -                        | Postgres connection string                          |
| `JWT_SECRET_KEY`     | yes      | -                        | Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM`      | no       | `HS256`                  |                                                       |
| `JWT_EXPIRE_MINUTES` | no       | `60`                     | Admin token lifetime                                 |
| `CORS_ORIGINS`       | no       | `http://localhost:5173` | Comma-separated list of allowed origins              |

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # then set VITE_API_BASE_URL if not localhost:8000
npm run dev
```

Serves on `http://localhost:5173`.

## Tests

```bash
cd backend
source venv/bin/activate
python -m pytest -q
```

Covers: entry validation/dedup, admin auth (login, token expiry/tampering,
protected routes), draw execution (seed replay reproducibility, distinct
winners, locking a completed draw, winner_count exceeding the entry pool,
audit ordering), the results endpoint (latest completed draw, PII
exclusion, empty state, most-recent-of-multiple), and a regression test
for the draw status enum's database CHECK constraint.

## Admin accounts

There is no signup endpoint. The only way to create an admin is:

```bash
cd backend
source venv/bin/activate
DATABASE_URL=<target-database-url> python scripts/create_admin.py <username>
```

It prompts for a password (hidden input, confirmed, minimum 8 characters)
and hashes it with bcrypt before inserting.

## Deployment

- **Backend**: Railway (or any host that can run `uvicorn` against a
  Postgres instance). Run `alembic upgrade head` against the target
  `DATABASE_URL` before first use, then seed an admin as above.
- **Frontend**: Vercel. `vercel.json` rewrites all paths to `index.html`
  so client-side routes (`/results`, `/admin`, etc.) work on refresh.
  Set `VITE_API_BASE_URL` to the deployed backend URL in the Vercel
  project's environment variables.
- Set the backend's `CORS_ORIGINS` to include the deployed frontend
  origin.

## Security notes

- Passwords are bcrypt-hashed; admin JWTs are signed with a secret read
  from the environment (never hardcoded) and carry an expiry.
- Login returns the same error for an unknown username and a wrong
  password, and checks a dummy hash on an unknown username so both
  cases take the same amount of time — this avoids leaking which
  users exist via timing.
- `get_current_admin` re-fetches the admin from the database on every
  request, so a deleted or renamed admin can't keep using an old token.
- Identifiers (email/CNIC) are never returned by any endpoint except
  the admin-only entry list, and never appear there either — only
  `id`, `name`, and `created_at` are exposed.
- A draw's seed is persisted before selection runs, so a draw's audit
  trail (seed, status, timestamps) exists even if the draw fails
  partway through.
