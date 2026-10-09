<div align="center">

# Issue Tracker API

**Projects, issues, and comments for a small team, with role-based access control.**

Built with FastAPI, SQLAlchemy 2.0 (async), Pydantic, PostgreSQL, Alembic, and JWT auth.

[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-90%20passing-success.svg)](#testing)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

[Quickstart](#quickstart) · [Configuration](#configuration) · [API](#api) · [Roles](#roles) · [Architecture](#architecture) · [Development](#development)

</div>

---

## Features

- **JWT authentication** with bcrypt-strength Argon2id password hashing
- **Three roles** — admin, manager, member — resolved from a permission matrix
- **Projects** with owners and team membership
- **Issues** with status, priority, assignee, creator, and due date
- **Comments** on issues, with edit/delete rules per role
- **Filtering, search, and pagination** on the issue list
- **Rate limiting** and per-account lockout with exponential backoff on repeated login failures
- **Async throughout** — `asyncpg`, async SQLAlchemy sessions, no sync database calls on the request path

---

## Quickstart

### Prerequisites

- Python 3.13+
- PostgreSQL 14+
- [`uv`](https://docs.astral.sh/uv/)

### 1. Install

```bash
uv sync
```

### 2. Configure

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

You need at minimum:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs JWTs. Must be **at least 32 bytes**; the app refuses to start otherwise. Generate one with `openssl rand -base64 48` |
| `DATABASE_URL` | Postgres connection string |
| `ADMIN_USERNAME` | First admin account to seed |
| `ADMIN_PASSWORD` | Password for that account. Leave empty to skip seeding |
| `ADMIN_EMAIL` | Email for that account |

### 3. Create the database

```bash
createdb issue_tracker
```

### 4. Run migrations

```bash
uv run alembic upgrade head
```

### 5. Start the server

```bash
uv run uvicorn app.main:app --reload
```

The first admin is created automatically on startup from the `ADMIN_*` variables.
Open <http://localhost:8000/docs> for interactive OpenAPI docs.

> The seeding hook skips any account that already exists. Changing `ADMIN_PASSWORD`
> afterwards does **not** rotate a live password — delete the row to re-seed.

---

## Configuration

Configuration is read from a `.env` file via `pydantic-settings`. The file used depends on
the `ENV_FILE` environment variable, defaulting to `.env`.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SECRET_KEY` | yes | — | JWT signing key. Minimum 32 bytes |
| `DATABASE_URL` | no | local Postgres | Async SQLAlchemy URL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | Token lifetime |
| `ADMIN_USERNAME` | no | `""` | Seeded admin username |
| `ADMIN_PASSWORD` | no | `""` | Seeded admin password. Empty disables seeding |
| `ADMIN_EMAIL` | no | `""` | Seeded admin email |
| `ENV_FILE` | no | `.env` | Which env file to load |

---

## API

All routes are prefixed with `/api/v1`. Authenticated routes expect
`Authorization: Bearer <access_token>`.

### Auth

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/auth/login` | Exchange credentials for a token |

### Users

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/users` | List users *(admin)* |
| `POST` | `/users` | Create a user |
| `GET` | `/users/me` | Current user's profile |
| `PATCH` | `/users/me` | Update own profile or password |
| `DELETE` | `/users/me` | Delete own account |
| `GET` | `/users/{id}` | Fetch a user by id |
| `PATCH` | `/users/{id}` | Update another user *(admin)* |
| `DELETE` | `/users/{id}` | Delete another user *(admin)* |
| `PATCH` | `/users/{id}/disable` | Disable a user *(admin)* |

### Projects

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/projects` | Projects you belong to |
| `POST` | `/projects` | Create a project |
| `GET` | `/projects/{id}` | Project detail |
| `PATCH` | `/projects/{id}` | Update a project |
| `POST` | `/projects/{id}/members/{user_id}` | Add a member |
| `DELETE` | `/projects/{id}/members/{user_id}` | Remove a member |

### Issues

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/projects/{id}/issues` | List issues — supports filtering and pagination |
| `POST` | `/projects/{id}/issues` | Create an issue |
| `GET` | `/issues/{id}` | Issue detail |
| `PATCH` | `/issues/{id}` | Update an issue |
| `DELETE` | `/issues/{id}` | Delete an issue |

Query parameters on the issue list: `search`, `status`, `priority`, `assignee_id`,
`creator_id`, `skip`, `limit`.

### Comments

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/issues/{id}/comments` | Comments on an issue |
| `POST` | `/issues/{id}/comments` | Add a comment |
| `PATCH` | `/comments/{id}` | Edit a comment |
| `DELETE` | `/comments/{id}` | Delete a comment |

---

## Roles

Permissions come from a single matrix in `app/permissions.py`.

| Capability | Admin | Manager | Member |
| --- | :---: | :---: | :---: |
| Manage users | ✅ | ❌ | ❌ |
| Create project | ✅ | ✅ | ❌ |
| Manage project members | ✅ | ✅ | ❌ |
| Create issue | ✅ | ✅ | ✅ |
| Update any issue | ✅ | ✅ | own / assigned |
| Delete issue | ✅ | ✅ | creator only |
| Delete any comment | ✅ | ✅ | own only |

A manager's reach is scoped to projects they belong to. The one exception to the
"own only" rules is comment deletion, which a manager may do within their projects.

Admins cannot change their own role — that guard exists so the last admin cannot
lock everyone out of the system.

---

## Architecture

```
app/
├── core/          Settings, logging, constants
├── db.py          Engine, session factory, Base
├── enums/         Role, IssueStatus, Priority, ProjectStatus
├── exceptions/    Domain exceptions and FastAPI handlers
├── models/        SQLAlchemy models
├── schemas/       Pydantic request/response models
├── permissions.py Role → permission matrix
├── rate_limit.py  IP throttle + per-account lockout
├── security.py    Password hashing, JWT creation
├── services/      Business logic
└── routers/       HTTP layer
```

**Request flow:** router → dependency resolution (auth, permissions, rate limits) →
service → database. Business rules live in services; routers stay thin.

Authorization is enforced in two layers: coarse route-level guards via
`require_permission(...)`, and finer relationship checks inside services, where
project membership and ownership are actually known.

---

## Development

### Testing

```bash
uv run pytest
```

Tests run against a **separate** database (`DATABASE_URL` in `.env.test`) and truncate
it between tests. `tests/conftest.py` asserts the database name ends in `_test` and
refuses to run otherwise, so a misconfigured environment cannot wipe your dev data.

```bash
uv run pytest --cov=app --cov-report=term-missing
```

### Linting and type checking

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

### Migrations

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

---

## Security notes

- Passwords are hashed with Argon2id and validated for length and for not containing
  the username.
- Login responses are constant-time with respect to whether a username exists, so
  account existence cannot be probed by timing.
- Failed logins lock an account with exponential backoff (1s doubling, capped at 60s).
  The counter is keyed on the account, not the source IP, so rotating IPs does not
  reset it.
- `SECRET_KEY` has no default. The application refuses to start without a real one.

---

## License

MIT — see [LICENSE](LICENSE).