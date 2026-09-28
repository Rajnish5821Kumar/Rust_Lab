# Development setup

## Prerequisites

- Python 3.12+ (CI uses 3.13)
- Node.js 24, or 22.22 or newer (some test dependencies require it)
- Docker with Compose v2, for PostgreSQL and Redis or the whole stack

## Option A: everything in Docker

```bash
cp .env.example .env        # then set POSTGRES_PASSWORD and JWT_SECRET
docker compose up --build
```

`backend/app`, `backend/alembic` and `frontend/src` are mounted into the containers, so
code changes reload automatically. Migrations run each time the `api` container starts.

## Option B: run the apps on the host

Start only the infrastructure:

```bash
docker compose up postgres redis
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The backend reads `../.env` (the repository root) and then `backend/.env`. Uncomment
`DATABASE_URL` and `REDIS_URL` in your `.env` so they point at `localhost`, then:

```bash
alembic upgrade head
uvicorn app.main:app --reload
celery -A app.workers.celery_app worker --loglevel=INFO   # in another terminal
```

On Windows, Celery's default prefork pool is unsupported. Add `--pool=solo` when you run
the worker outside Docker.

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173; /api is proxied to http://localhost:8000
```

Set `VITE_API_PROXY_TARGET` to proxy to a different API address.

### CLI

```bash
cd cli
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
devvault health
```

## Everyday commands

| Task | Command (from the package directory) |
| --- | --- |
| Backend tests | `pytest` |
| Backend lint / format / types | `ruff check .` / `ruff format .` / `mypy` |
| New migration | `alembic revision --autogenerate -m "describe change"` |
| Frontend tests | `npm test` (`npm run test:watch` while developing) |
| Frontend lint / format / types | `npm run lint` / `npm run format` / `npm run typecheck` |

## Tip: OneDrive and synced folders

If the repository lives in a synced folder (OneDrive, Dropbox), `npm install` and virtualenv
creation can be very slow because every file in `node_modules/` and `.venv/` gets synced.
Keep the checkout outside synced folders if you can.
