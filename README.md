# BallotBox

A multi-product raffle/ballot system: an admin creates one or more
**products** (raffle events), the public enters a name plus an email
and/or CNIC against a product, and an admin runs a seeded, reproducible
random draw per product and exports the results.

## How it works

- **Products** — an admin creates a product with a name and an optional
  scheduled closing time (`closes_at`). A product accepts entries while
  it's *effectively open*: its manual `is_open` switch is on **and**
  either it has no `closes_at` or that time hasn't passed yet. An admin
  can also flip `is_open` off at any time to close entries early,
  independent of any schedule.
- **Entry** — anyone submits `name` + a product + an email and/or a
  13-digit Pakistani CNIC (at least one identifier is required) via the
  public entry form. A closed product rejects new entries. Duplicate
  identifiers *within the same product* are rejected; CNIC is normalized
  (digits-only) so `12345-1234567-1` and `1234512345671` dedupe against
  each other.
- **Draw** — an admin picks a `winner_count` and runs a draw for a
  product. The service generates a random seed, **persists it to the
  database before any selection happens** (the audit anchor), then seeds
  `random.Random(seed)` and samples winners from that product's
  candidates sorted by id. Given the same seed and candidate set, the
  selection is exactly reproducible. A completed draw is immutable —
  re-running it is rejected; a redo creates a brand-new draw row with a
  new seed, and both stay on record permanently. Draws are scoped per
  product — winning (or entering) one product never affects another.
- **Exports** — admins download a product's candidate list as CSV, and a
  completed draw's winners as a PDF. There is no public results page;
  winners are only visible to admins via these exports.
- **Bulk upload** — admins can create many products at once from a CSV
  (a single `name` column). A row is skipped, never fails the whole
  upload, if its name is blank, a duplicate within the file, or already
  exists — each with its own reported reason.
- **Admin accounts** — any admin can create or delete other admin
  accounts. An admin can't delete their own account, and the last
  remaining admin account can never be deleted.
- **Ballot reset** — a destructive, admin-only action that deletes every
  product, candidate, draw, and winner (admin accounts are untouched),
  for starting a new event from zero. Requires typing a confirmation
  phrase.

## Architecture

Backend is a layered FastAPI app; each slice (products, candidates,
draws, auth, admin accounts) follows the same shape:

```
routes/       FastAPI routers — HTTP concerns and status codes only
services/     business logic (draw selection, CSV/PDF export, bulk
              upload, admin account rules, ballot reset)
repositories/ all database access (SQLAlchemy queries)
schemas/      Pydantic v2 request/response models
models/       SQLAlchemy ORM tables
core/         security primitives (JWT, password hashing) and the
              get_current_admin auth dependency
```

Frontend is a React + Vite app with client-side routing
(`react-router-dom`):

```
/                            public entry form
/admin/login                 admin login
/admin                       admin dashboard (protected)
/admin/products               products list (protected)
/admin/products/new           create product (protected)
/admin/products/:productId    product detail — candidates, draws, exports (protected)
/admin/controls               admin accounts + ballot reset (protected)
```

All `/admin/*` routes except `/admin/login` bounce to `/admin/login`
without a valid token.

### Data model

- `products` — id, name (case-insensitively unique), is_open, closes_at,
  created_at
- `candidates` — id, product_id, name, email, cnic, created_at (dedup on
  cnic or email, scoped per product)
- `draws` — id, product_id, seed, winner_count, status
  (pending/completed/failed), drawn_at
- `winners` — join table: draw_id, candidate_id, position (unique per
  draw)
- `admins` — id, username, password_hash (bcrypt)

### Endpoints

| Method | Path                                   | Auth  | Notes                                                       |
|--------|-----------------------------------------|-------|--------------------------------------------------------------|
| POST   | `/auth/login`                          | -     | Returns a JWT                                                 |
| GET    | `/auth/me`                             | admin | Confirms the current token                                    |
| GET    | `/admin/users`                         | admin | Lists admin accounts                                           |
| POST   | `/admin/users`                         | admin | Creates an admin account                                       |
| DELETE | `/admin/users/{id}`                    | admin | Deletes an admin account (not self, not the last one)          |
| POST   | `/admin/reset`                         | admin | Deletes every product/candidate/draw/winner (confirm required) |
| GET    | `/products/public`                     | -     | Open products, for the public entry form's dropdown            |
| GET    | `/products/summary`                    | admin | Dashboard counts (products, open products, candidates)         |
| POST   | `/products`                            | admin | Creates a product                                               |
| POST   | `/products/bulk-upload`                | admin | Creates many products from a CSV                                |
| GET    | `/products`                            | admin | Lists all products                                              |
| GET    | `/products/{id}`                       | admin | One product                                                     |
| POST   | `/products/{id}/open`                  | admin | Toggles `is_open`                                               |
| POST   | `/products/{id}/closes-at`             | admin | Sets or clears the scheduled closing time                       |
| GET    | `/products/{id}/candidates`            | admin | Lists a product's candidates                                    |
| GET    | `/products/{id}/candidates/export`     | admin | Downloads candidates as CSV                                     |
| DELETE | `/products/{id}`                       | admin | Deletes a product and everything under it                       |
| DELETE | `/products/{id}/candidates`            | admin | Clears a product's candidates (and its draw history)             |
| POST   | `/candidates`                          | -     | Submits an entry                                                 |
| POST   | `/products/{id}/draws`                 | admin | Runs a new draw                                                  |
| GET    | `/products/{id}/draws`                 | admin | Lists a product's draws                                          |
| GET    | `/products/{id}/draws/{drawId}`        | admin | One draw with its winners                                        |
| DELETE | `/products/{id}/draws`                 | admin | Clears a product's draw history (candidates are kept)             |
| GET    | `/products/{id}/draws/{drawId}/export` | admin | Downloads a completed draw's winners as PDF                      |
| GET    | `/health`                              | -     | Health check                                                     |

## Project layout

```
backend/
  app/                FastAPI application (see Architecture above)
  alembic/             database migrations
  scripts/create_admin.py   seeds the first admin account
  tests/               pytest suite
  requirements.txt      runtime dependencies (incl. fpdf2 for PDF export)
  requirements-dev.txt   + pytest, httpx, pypdf (for PDF export tests)
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

Covers: admin accounts (create/delete, self-delete and last-admin
guards), admin auth (login, token expiry/tampering, protected routes),
ballot reset (including foreign-key delete ordering), candidate
validation/dedup and CSV export, candidate submission routes, draw
execution (seed replay reproducibility, multi-winner draws, locking a
completed draw, winner_count exceeding the candidate pool), the draw
status enum's database CHECK constraint, draw routes (incl. PDF export),
products CRUD, the open/closed toggle, the scheduled `closes_at`
open/close logic, the products dashboard summary, and bulk product
upload (skips and reasons).

## Admin accounts

There's no public signup. Before any admin can log in, seed the first
one directly against the database:

```bash
cd backend
source venv/bin/activate
DATABASE_URL=<target-database-url> python scripts/create_admin.py <username>
```

It prompts for a password (hidden input, confirmed, minimum 8 characters)
and hashes it with bcrypt before inserting. Once at least one admin
exists, further admin accounts can be created and deleted from **Admin
controls** in the app — an admin can never delete their own account or
the last remaining one.

## Deployment

- **Backend**: Railway (or any host that can run `uvicorn` against a
  Postgres instance). Run `alembic upgrade head` against the target
  `DATABASE_URL` before first use, then seed an admin as above.
- **Frontend**: Vercel. `vercel.json` rewrites all paths to `index.html`
  so client-side routes (`/admin/products/:id`, etc.) work on refresh.
  Set `VITE_API_BASE_URL` to the deployed backend URL in the Vercel
  project's environment variables.
- Set the backend's `CORS_ORIGINS` to include the deployed frontend
  origin. The API also explicitly exposes the `Content-Disposition`
  header via CORS so the frontend can read a downloaded file's name for
  the CSV/PDF exports.

## Security notes

- Passwords are bcrypt-hashed; admin JWTs are signed with a secret read
  from the environment (never hardcoded) and carry an expiry.
- Login returns the same error for an unknown username and a wrong
  password, and checks a dummy hash on an unknown username so both
  cases take the same amount of time — this avoids leaking which
  users exist via timing.
- `get_current_admin` re-fetches the admin from the database on every
  request, so a deleted or renamed admin can't keep using an old token.
- Identifiers (email/CNIC) are never returned by any endpoint except a
  product's admin-only candidate list.
- A draw's seed is persisted before selection runs, so a draw's audit
  trail (seed, status, timestamps) exists even if the draw fails
  partway through.
- Admin-entered product names are free text; before being placed in a
  downloaded file's `Content-Disposition` header (CSV/PDF exports),
  they're stripped to a safe ASCII slug so quotes, newlines, or unicode
  in a name can't break or inject into the header.
