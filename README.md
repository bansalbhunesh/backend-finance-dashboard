# Finance Dashboard Backend

A small **FastAPI** service with **SQLite** persistence, **JWT bearer authentication**, and **role-based access control** for a finance dashboard. It covers user and role management, financial record CRUD with filters, aggregated dashboard endpoints, validation, and consistent error responses.

Interactive API docs: run the server and open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (or your chosen host/port).

## Assumptions and tradeoffs

- **Global ledger**: Financial records are shared across the organization. **Analyst** and **admin** users see the same dataset when listing or filtering records. The `created_by_user_id` field records who created a row for audit purposes only; it is not used to hide rows from other authorized users. A multi-tenant or per-user ledger would add a `tenant_id` or `owner_id` and scope every query accordingly.
- **Viewer role**: Can call **dashboard** endpoints only (summary aggregates and recent activity in `/dashboard/full`). They **cannot** access `/records`, matching the brief (“view dashboard data” only).
- **Persistence**: Default **SQLite** file (`finance.db`) for easy local setup. Swap `DATABASE_URL` for PostgreSQL or another SQLAlchemy-supported URL when needed.
- **Auth**: **JWT** signed with `HS256`. This is suitable for the assignment; production systems would add refresh tokens, key rotation, and HTTPS-only delivery.
- **Trend periods**: Monthly and weekly buckets use SQLite `strftime` (`%Y-%m` and `%Y-%W`). Week boundaries follow SQLite’s rules, not necessarily ISO week labels.

## Roles and permissions

| Capability | Viewer | Analyst | Admin |
|------------|--------|---------|-------|
| `GET /dashboard/summary`, `GET /dashboard/full` | Yes | Yes | Yes |
| `GET /records`, `GET /records/{id}` | No | Yes | Yes |
| `POST /PATCH /DELETE /records` | No | No | Yes |
| `GET/PATCH/DELETE /users/*`, `POST /users` | No | No | Yes |
| `GET /users/me` | Yes | Yes | Yes |

Inactive users (`is_active=false`) cannot obtain a token and are rejected if already authenticated.

## Setup

Requires **Python 3.11+** (3.11–3.12 recommended if dependency wheels are missing on very new Python versions).

```bash
cd finance-dashboard-backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL`.

## Run

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first startup the app creates tables and, if there are no users, **seeds** demo accounts and sample transactions.

### Demo logins (after seed)

| Email | Password | Role |
|-------|----------|------|
| `admin@example.com` | `Admin12345!` | admin |
| `analyst@example.com` | `Analyst12345!` | analyst |
| `viewer@example.com` | `Viewer12345!` | viewer |

## API overview

- **`POST /auth/login`** — JSON `{ "email", "password" }` → `{ "access_token", "token_type": "bearer" }`. Use header `Authorization: Bearer <token>` on other routes.
- **`GET /users/me`** — Current user profile.
- **`GET /users`, `POST /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}`** — Admin only. Create user expects `email`, `password` (min 8 chars), optional `full_name`, `role`, `is_active`.
- **`GET /records`** — Analyst/admin. Query params: `date_from`, `date_to`, `category`, `type` (`income` | `expense`), `skip`, `limit` (max 200).
- **`GET /records/{id}`** — Analyst/admin.
- **`POST /records`** — Admin. Body: `amount` (> 0), `type`, `category`, `occurred_at` (ISO datetime), optional `notes`.
- **`PATCH /records/{id}`, `DELETE /records/{id}`** — Admin.
- **`GET /dashboard/summary`** — Totals: income, expenses, net balance, record count.
- **`GET /dashboard/full`** — Summary plus category totals, recent activity (`recent_limit`), and trends (`trend_granularity=month|week`).

### Validation and errors

- Request bodies are validated with **Pydantic** (e.g. positive `amount`, email format, enum values).
- **422** responses include `detail` (machine-readable errors) and a short `message` for validation failures.
- **401** for missing/invalid tokens; **403** when the role is not allowed; **404** for missing resources; **409** for duplicate emails on user create/update.

## Project layout

- `app/main.py` — App factory, lifespan (migrations via `create_all` + seed), validation error handler.
- `app/models.py` — SQLAlchemy models and enums.
- `app/schemas.py` — Pydantic request/response models.
- `app/security.py` — Password hashing (`bcrypt`) and JWT create/decode.
- `app/deps.py` — `get_current_user` and `require_roles` helpers.
- `app/routers/` — Route modules: `auth`, `users`, `records`, `dashboard`.
- `app/seed.py` — Idempotent demo data when the user table is empty.

## Optional enhancements (not implemented here)

Pagination is partially covered via `skip`/`limit` on records. Further improvements could include refresh tokens, soft deletes, rate limiting, pytest coverage, and Alembic migrations for production schema evolution.
