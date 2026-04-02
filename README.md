# Backend — Finance Dashboard API

Backend for a finance dashboard: **users and roles**, **financial records (CRUD + filters)**, **dashboard summaries**, and **role-based access control**. Built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

**Repository:** [github.com/bansalbhunesh/backend-finance-dashboard](https://github.com/bansalbhunesh/backend-finance-dashboard)

---

## Contents

1. [Features](#features)
2. [Quick start](#quick-start)
3. [Try the API](#try-the-api)
4. [Roles and permissions](#roles-and-permissions)
5. [API reference (short)](#api-reference-short)
6. [Configuration](#configuration)
7. [Assumptions](#assumptions)
8. [Project structure](#project-structure)
9. [Errors and validation](#errors-and-validation)

---

## Features

- JWT bearer authentication (`Authorization: Bearer <token>`)
- Three roles: **viewer**, **analyst**, **admin** — enforced on every protected route
- Financial **transactions**: amount, type (`income` / `expense`), category, date, notes
- **Dashboard** totals, category breakdowns, recent activity, monthly/weekly trends
- Input validation (Pydantic) and consistent HTTP status codes
- Local **SQLite** database; optional `.env` for secrets and database URL

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
| GET, PATCH, DELETE | `/users/{id}` | Admin | Get / update / delete user |
| GET | `/records` | Analyst, Admin | List with filters (see below) |
| GET | `/records/{id}` | Analyst, Admin | Single record |
| POST, PATCH, DELETE | `/records`, `/records/{id}` | Admin | Create / update / delete |
| GET | `/dashboard/summary` | All roles | Income, expenses, net, count |
| GET | `/dashboard/full` | All roles | Summary + categories + recent + trends |

**List filters** (`GET /records`): `date_from`, `date_to`, `category`, `type` (`income` \| `expense`), `skip`, `limit` (max `200`).

**Create record** (`POST /records`): `amount` (must be positive), `type`, `category`, `occurred_at` (ISO 8601), optional `notes`.

**Dashboard full** (`GET /dashboard/full`): optional `recent_limit` (default `10`), `trend_granularity` = `month` or `week`.

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
- **Viewer scope:** Viewers match the assignment idea of “dashboard only”: they **cannot** call `/records`.
- **SQLite:** Single-file database (`finance.db`). It is listed in `.gitignore` so it is not committed; each clone gets a fresh DB and seed on first run.
- **Trend buckets:** Month/week groups use SQLite `strftime` (`%Y-%m`, `%Y-%W`). Week labels follow SQLite, not necessarily ISO week numbers.
- **Auth model:** JWT with `HS256`. Refresh tokens, key rotation, and HTTPS are out of scope for this exercise.

---

## Project structure

```
app/
  main.py          # FastAPI app, lifespan (create tables + seed), validation errors
  config.py        # Settings (env / defaults)
  database.py      # Engine, session, Base
  models.py        # User, FinancialRecord, enums
  schemas.py       # Pydantic request/response models
  security.py      # bcrypt passwords, JWT encode/decode
  deps.py          # Current user + role guards
  seed.py          # Demo users + sample data (runs if DB has no users)
  routers/
    auth.py        # Login
    users.py       # User CRUD + /me
    records.py     # Record CRUD + filters
    dashboard.py   # Summary + aggregates
```

---

## Errors and validation

| Code | When |
|------|------|
| **401** | Missing or invalid token, bad login |
| **403** | Wrong role for the action, or inactive user |
| **404** | User or record not found |
| **409** | Duplicate email on user create/update |
| **422** | Invalid body or query (Pydantic); response includes `detail` and `message` |

---

## Optional next steps (not in this repo)

Refresh tokens, soft deletes, rate limiting, Alembic migrations, automated tests, or deploying behind HTTPS with secrets from the host environment.
