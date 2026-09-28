# 3. Async SQLAlchemy 2 with asyncpg for the API

- Status: Accepted
- Date: 2026-09-28

## Context

FastAPI supports both sync handlers (run in a thread pool) and async handlers. DevVault's
API will make many I/O-bound calls: PostgreSQL, Redis, and later the GitHub API through
httpx.

## Decision

Use SQLAlchemy 2's asyncio extension with the `asyncpg` driver in the API. Sessions come
from a request-scoped dependency (`app.db.session.get_db`), and services commit explicitly.
Sessions use `expire_on_commit=False`, and timestamps have Python-side defaults, so
attributes can be read after commit without implicit I/O, which async sessions don't allow.

Tests run against in-memory SQLite (`aiosqlite`) by default for speed. CI runs the same
suite against PostgreSQL.

## Consequences

- Handlers never block the event loop on database calls.
- Lazy loading is unavailable in async code. Relationships must be eager-loaded
  deliberately, which also guards against N+1 queries.
- Celery tasks are synchronous. When workers need the database (Phase 2), they will either
  run async code with `asyncio.run` or use a separate sync engine. That choice will be
  recorded in its own ADR.
- SQLite and PostgreSQL differ (for example, SQLite drops time zones and ignores
  `FOR UPDATE`). Code normalises timestamps, and CI's PostgreSQL run catches remaining
  differences.
