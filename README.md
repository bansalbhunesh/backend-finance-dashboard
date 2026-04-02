# Backend — Finance Dashboard API

Backend for a finance dashboard: **users and roles**, **financial records (CRUD + filters)**, **dashboard summaries**, and **role-based access control**. Built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

**Repository:** [github.com/bansalbhunesh/backend-finance-dashboard](https://github.com/bansalbhunesh/backend-finance-dashboard)

---

## Contents

1. [Features](#features)
2. [Quick start](#quick-start)
3. [Docker](#docker)
4. [Try the API](#try-the-api)
5. [Roles and permissions](#roles-and-permissions)
6. [API reference (short)](#api-reference-short)
7. [Running tests](#running-tests)
8. [Configuration](#configuration)
9. [Assumptions](#assumptions)
10. [Project structure](#project-structure)
11. [Errors and validation](#errors-and-validation)

---

## Features

- JWT bearer authentication (`Authorization: Bearer <token>`)
- Three roles: **viewer**, **analyst**, **admin** — enforced on every protected route
- Financial **transactions**: amount, type (`income` / `expense`), category, date, notes
- **Dashboard** totals, category breakdowns, recent activity, monthly/weekly trends
- **Soft delete** for users and records (data preserved, excluded from queries)
- **Pagination** with metadata (`total`, `page`, `pages`, `limit`)
- **Search** across notes and category fields
- **Rate limiting** (60 requests/minute per IP via SlowAPI)
- **Structured logging** with request duration tracking
- Input validation (Pydantic) and consistent HTTP status codes
- Local **SQLite** database; optional `.env` for secrets and database URL
- **Docker** support for containerised deployment
- **41 unit tests** covering auth, users, records, and dashboard

---

## Quick start

**Requirements:** Python **3.11+** (3.11 or 3.12 recommended if installs fail on very new Python versions).

```bash
git clone https://github.com/bansalbhunesh/backend-finance-dashboard.git
cd backend-finance-dashboard

python -m venv .venv
# Windows:
#   .venv\Scripts\activate
# macOS / Linux:
#   source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**First run:** tables are created automatically. If the database has **no users**, demo accounts and sample transactions are **seeded** once.

**Interactive docs:** after starting the server, open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## Docker

Build and run the API in a single command:

```bash
docker compose up --build
```

Or run manually:

```bash
docker build -t finance-api .
docker run -p 8000:8000 finance-api
```

The API will be available at `http://localhost:8000`.

---

## Try the API

### 1. Log in

`POST /auth/login` with JSON body:

```json
{ "email": "admin@example.com", "password": "Admin12345!" }
```

Response includes `access_token`. Use it on all other endpoints:

```http
Authorization: Bearer <paste_token_here>
```

### 2. Demo accounts (after seed)

| Email | Password | Role |
|-------|----------|------|
| `admin@example.com` | `Admin12345!` | Full access (users + records) |
| `analyst@example.com` | `Analyst12345!` | Read records + dashboard |
| `viewer@example.com` | `Viewer12345!` | Dashboard only |

These are **local demo credentials** for grading and development, not production users.

### 3. Quick checks

- **Health:** `GET /health` — no auth.
- **Profile:** `GET /users/me` — requires token.
- **Dashboard:** `GET /dashboard/summary` — any logged-in role.

---

## Roles and permissions

| What | Viewer | Analyst | Admin |
|------|:------:|:-------:|:-----:|
| Dashboard (`GET /dashboard/summary`, `GET /dashboard/full`) | Yes | Yes | Yes |
| List / get records (`GET /records`, `GET /records/{id}`) | No | Yes | Yes |
| Create / update / delete records | No | No | Yes |
| Manage users (`/users` except `/users/me`) | No | No | Yes |
| Current user (`GET /users/me`) | Yes | Yes | Yes |

Users with `is_active: false` cannot log in and are rejected if a token still exists.

---

## API reference (short)

| Method | Path | Who | Purpose |
|--------|------|-----|---------| 
| POST | `/auth/login` | Public | Email + password → JWT |
| GET | `/users/me` | Authenticated | Current user |
| GET, POST | `/users` | Admin | List / create users |
| GET, PATCH, DELETE | `/users/{id}` | Admin | Get / update / soft-delete user |
| GET | `/records` | Analyst, Admin | List with filters + pagination (see below) |
| GET | `/records/{id}` | Analyst, Admin | Single record |
| POST, PATCH, DELETE | `/records`, `/records/{id}` | Admin | Create / update / soft-delete |
| GET | `/dashboard/summary` | All roles | Income, expenses, net, count |
| GET | `/dashboard/full` | All roles | Summary + categories + recent + trends |

**List filters** (`GET /records`): `date_from`, `date_to`, `category`, `type` (`income` \| `expense`), `search`, `page` (1-indexed), `limit` (max `200`).

**Pagination response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "pages": 8,
  "limit": 20
}
```

**Create record** (`POST /records`): `amount` (must be positive), `type`, `category`, `occurred_at` (ISO 8601), optional `notes`.

**Dashboard full** (`GET /dashboard/full`): optional `recent_limit` (default `10`), `trend_granularity` = `month` or `week`.

---

## Running tests

The project includes **41 unit tests** covering authentication, users, records, and dashboard endpoints.

```bash
# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests with verbose output
python -m pytest tests/ -v
```

Tests use an **in-memory SQLite** database and are fully isolated — no external services required.

---

## Configuration

Copy `.env.example` to `.env` if you want to override defaults.

| Variable | Purpose | Default |
|----------|---------|---------| 
| `SECRET_KEY` | JWT signing key | Dev default in `app/config.py` — **change for any shared or deployed environment** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` (24h) in example |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./finance.db` |

**Submission / local grading:** no external API keys are required. Use a strong `SECRET_KEY` only if you expose the API beyond your machine.

---

## Assumptions

- **Shared ledger:** All analysts and admins see the **same** financial records. `created_by_user_id` is for **audit** (who created the row), not row-level privacy. A production multi-tenant app would add something like `tenant_id` or `owner_id` and filter every query.
- **Viewer scope:** Viewers match the assignment idea of "dashboard only": they **cannot** call `/records`.
- **Soft delete:** Deleted records and users are preserved in the database with `is_deleted = True`. They are excluded from all queries, lists, and dashboard aggregations.
- **SQLite:** Single-file database (`finance.db`). It is listed in `.gitignore` so it is not committed; each clone gets a fresh DB and seed on first run.
- **Trend buckets:** Month/week groups use SQLite `strftime` (`%Y-%m`, `%Y-%W`). Week labels follow SQLite, not necessarily ISO week numbers.
- **Auth model:** JWT with `HS256`. Refresh tokens, key rotation, and HTTPS are out of scope for this exercise.
- **Rate limiting:** 60 requests per minute per IP address. Configurable via SlowAPI.

---

## Project structure

```
app/
  main.py            # FastAPI app, lifespan, rate limiting, request logging
  config.py          # Settings (env / defaults)
  database.py        # Engine, session, Base
  models.py          # User, FinancialRecord, enums (with soft delete)
  schemas.py         # Pydantic request/response models (with pagination)
  security.py        # bcrypt passwords, JWT encode/decode
  deps.py            # Current user + role guards
  seed.py            # Demo users + sample data (runs if DB has no users)
  logging_config.py  # Structured logging setup
  routers/
    auth.py          # Login
    users.py         # User CRUD + /me (soft delete)
    records.py       # Record CRUD + filters + search + pagination (soft delete)
    dashboard.py     # Summary + aggregates (excludes soft-deleted)
tests/
  conftest.py        # Shared fixtures (in-memory DB, test client, auth helpers)
  test_auth.py       # Auth endpoint tests
  test_users.py      # User CRUD + role restriction tests
  test_records.py    # Record CRUD, filtering, search, pagination tests
  test_dashboard.py  # Dashboard summary + aggregation tests
Dockerfile           # Production container image
docker-compose.yml   # Single-command deployment
```

---

## Errors and validation

| Code | When |
|------|------|
| **400** | No fields to update, or self-deletion attempt |
| **401** | Missing or invalid token, bad login |
| **403** | Wrong role for the action, or inactive user |
| **404** | User or record not found (or soft-deleted) |
| **409** | Duplicate email on user create/update |
| **422** | Invalid body or query (Pydantic); response includes `detail` and `message` |
| **429** | Rate limit exceeded (60 requests/minute) |
