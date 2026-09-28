# Architecture

## Components

```
            ┌──────────────┐        ┌──────────────┐
 browser ──▶│  frontend    │──/api─▶│    api       │──▶ PostgreSQL
            │ Vite / nginx │        │  FastAPI     │
            └──────────────┘        └──────┬───────┘
                                           │ enqueue
 devvault CLI ────── HTTP /api ──────▶ api │
                                           ▼
                                    ┌──────────────┐
                                    │    Redis     │◀── worker (Celery)
                                    └──────────────┘        │
                                                            └──▶ PostgreSQL
```

| Component | Tech | Responsibility |
| --- | --- | --- |
| `backend/app` (api) | FastAPI, SQLAlchemy 2 async, Pydantic v2 | REST API, auth, validation, persistence |
| `backend/app/workers` (worker) | Celery on Redis | Long-running jobs (Git analysis, GitHub sync, scans, reports) in later phases |
| `frontend` | React 19, TypeScript, Vite, Tailwind CSS | Dashboard. The dev server proxies `/api` to the API; production uses nginx |
| `cli` | Typer, httpx | `devvault` command; talks to the API over HTTP |
| PostgreSQL | 17 | System of record |
| Redis | 7 | Celery broker and result backend; later caching and rate limiting |

The API and the worker share one codebase and one Docker image, so models and services are
never duplicated.

## Backend layers

Requests flow through the layers in one direction:

```
api/routes/*      HTTP only: parse input, call a service, shape the response
   │
services/*        Business rules and transactions (commit / rollback)
   │
repositories/*    SQLAlchemy queries; no business logic
   │
models/*          ORM tables
```

Supporting modules:

- `schemas/`: Pydantic request and response models (the public API contract).
- `core/config.py`: typed settings from environment variables.
- `core/security.py`: password hashing and token primitives.
- `core/errors.py`: domain exceptions; `api/errors.py` maps them to HTTP responses.
- `middleware/request_context.py`: request IDs, access logging, JSON 500s.
- `api/deps.py`: dependency injection for DB sessions, the current user, role checks and pagination.

Services receive an `AsyncSession` and commit explicitly. A request that raises before
committing is rolled back when its session closes.

## Cross-cutting behaviour

- **Errors.** Every non-2xx response has the form
  `{"error": {"code", "message", "details", "request_id"}}`. Validation errors list
  field locations but never echo submitted values, since they could be passwords.
- **Request IDs.** Each request gets an `X-Request-ID`. A safe ID from the caller is
  reused; otherwise a new one is generated. The ID is returned in the response, attached
  to every log line, and included in error bodies.
- **Logging.** JSON lines on stdout, one `request completed` entry per request with method,
  path, status and duration.
- **Configuration.** Environment variables only. Secrets have no defaults.

## Decisions

Significant choices are recorded as ADRs in [architecture/decisions](architecture/decisions/).
