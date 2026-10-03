# ez-file-storage

[![CI](https://github.com/KingAusti/ez-file-storage/actions/workflows/ci.yml/badge.svg)](https://github.com/KingAusti/ez-file-storage/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A self-hosted API service for storing personal text entries. Users register,
log in with a JWT, and create, search, tag and delete their own entries over
HTTP. There is no frontend in this repository; the OpenAPI docs at `/docs` are
the interface.

Stack: FastAPI, SQLAlchemy, Alembic, PostgreSQL (SQLite for local use), Redis, slowapi, structlog, nginx.

## Requirements

- Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) for local runs
- Docker with Compose for the containerised setup
- `pg_dump`, `psql` and `gzip` for the backup scripts

## Quick start

From a clone of the repository, run the API locally against SQLite:

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --port 8000
```

Open http://localhost:8000/docs. `ENVIRONMENT=development` (the default in
`.env.example`) creates the tables on startup. Redis is not needed locally; it
is only used by the `/health` check, which reports it as unhealthy when absent.

`start-dev.sh` does the same thing in one step (`uv run python main.py`, with
reload).

## Features

Endpoints, from `backend/app/main.py` and `backend/app/routers/`:

| Area | Endpoints |
| --- | --- |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`, `/auth/reset-password`; `GET /auth/me` |
| Data entries | `GET /data-entries/` (search, tag and date filters, sorting, limit/offset), `POST /data-entries/`, `GET`, `PUT`, `DELETE /data-entries/{id}` |
| Tags | `GET /tags/` (with usage counts), `POST /tags/`, `GET`, `PUT`, `DELETE /tags/{id}` |
| Service | `GET /`, `/version`, `/health`, `/metrics` |

- Login returns an access token and a refresh token (HS256 JWTs, 30 minute and
  7 day lifetimes by default). Refresh tokens are stored hashed and revoked on
  logout. Entries and tags routes require a bearer token, and entries are
  scoped to their owner.
- An account is locked for 15 minutes after 5 failed logins.
- Per-IP rate limits with slowapi, set per route (for example login 5/minute,
  entry reads 100/hour, entry writes 50/hour).
- Security-relevant actions (login, failed login, entry and tag changes) are
  written to an `audit_logs` table.
- Structured logs with structlog; optional Sentry reporting when `SENTRY_DSN`
  is set.
- `/metrics` is a placeholder that returns zeros, and `/auth/forgot-password`
  does not send email: no mail-sending code exists yet.

## Configuration

Local runs read `backend/.env` (template: `backend/.env.example`). Every key is
a field of `Settings` in `backend/app/core/config.py`; unset keys use the
defaults there.

| Key | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing key. Set your own. |
| `ALGORITHM` | JWT algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime, default 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime, default 7 |
| `DATABASE_URL` | SQLAlchemy URL for the app |
| `DATABASE_URL_ASYNC` | Async URL (`postgresql+asyncpg://`) |
| `REDIS_URL` | Redis URL, used by `/health` |
| `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_TLS`, `MAIL_SSL` | Declared, not used by any code yet |
| `SENTRY_DSN` | Enables Sentry when set |
| `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_LOGIN_ATTEMPTS` | Declared, not used; route limits are hard-coded |
| `ENVIRONMENT` | `development` creates tables on startup; any other value does not |
| `DEBUG` | `true` serves `/docs` and `/redoc`, allows any CORS origin, and echoes SQL |

With `DEBUG=false` there are no docs routes and no CORS origins are allowed.

Docker Compose reads the root `.env` (template: `.env.example`): `SECRET_KEY`,
`POSTGRES_PASSWORD`, `ENVIRONMENT`, `SENTRY_DSN` and the `MAIL_*` keys. Compose
sets `DATABASE_URL`, `DATABASE_URL_ASYNC` and `REDIS_URL` itself.

## Development

```bash
cd backend
uv sync --extra dev
SECRET_KEY=test ENVIRONMENT=testing uv run pytest
uv run black --check . && uv run isort --check-only . && uv run flake8 .
```

Tests run on SQLite and need no Docker. Migrations live in `backend/alembic/versions/`
and use the `sqlalchemy.url` set in `backend/alembic.ini`, not `DATABASE_URL`:

```bash
cd backend
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe the change"
```

`docker-compose.dev.yml` mounts `backend/` into the container and runs uvicorn
with `--reload`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

CI (`.github/workflows/ci.yml`) runs backend tests, a security scan and a
Docker build on pushes and pull requests to `main` and `develop`.

## Deployment

`docker-compose.yml` defines `postgres`, `redis` and `backend`, plus `nginx`
behind the `production` profile. The backend publishes port 8000, PostgreSQL
5432 and Redis 6379 on all interfaces, so put a firewall in front or change the
port mappings.

```bash
cp .env.example .env        # set SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build -d
docker compose --profile production up --build -d   # adds nginx
```

`./deploy.sh start`, `stop`, `restart`, `status`, `logs [service]` and
`cleanup` wrap the same commands. The script calls the `docker-compose`
binary, so it needs Compose v1 or a compatibility shim. `./setup.sh` generates
a root `.env` with random secrets and then runs `docker compose up`.

`nginx/nginx.conf` listens on port 80, rate limits `/api/` (10 requests/second)
and `/auth/` (5 requests/minute), and proxies everything to the backend. The
HTTPS server block is commented out; certificates would go in `nginx/ssl/`.

Compose does not run Alembic. With `ENVIRONMENT=production` the app does not
create tables, so run `alembic upgrade head` against the database first.

## Backups

`scripts/backup.sh [name]` writes a gzipped plain-SQL `pg_dump` to
`./backups/` (`BACKUP_DIR`), deletes backups older than 30 days
(`RETENTION_DAYS`) and optionally uploads to S3 when `S3_BUCKET` is set.
Connection settings come from `DB_HOST`, `DB_PORT`, `DB_NAME` and `DB_USER`
(defaults: localhost, 5432, data_storage, postgres).

```bash
./scripts/backup.sh
./scripts/restore.sh backups/backup_YYYYMMDD_HHMMSS.sql.gz
```

`scripts/restore.sh` loads the dump into a temporary database, asks for
confirmation twice, then drops and recreates the live database.

## License

MIT. See [LICENSE](LICENSE).
