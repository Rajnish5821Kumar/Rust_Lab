# Testing

## Backend (`backend/tests`, pytest + pytest-asyncio)

```bash
cd backend
pytest                          # in-memory SQLite (fast, no services needed)
pytest --cov                    # with coverage
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/devvault_test pytest
```

Setting `TEST_DATABASE_URL` runs the whole suite against PostgreSQL. CI does this on every
push. **Tables are dropped and recreated for each test, so use a throwaway database.**

| File | Covers |
| --- | --- |
| `test_health.py` | Health payload, readiness when dependencies are up or down, OpenAPI |
| `test_security.py` | Argon2 hashing, JWT expiry, signature, type and `alg=none` rejection, refresh token hashing |
| `test_config.py` | Required settings, secret length, env parsing, secret not in `repr` |
| `test_auth_api.py` | Registration rules, login (including uniform failure messages), rotation, reuse detection, expiry, logout |
| `test_users_api.py` | Profile, password change revoking sessions, RBAC, pagination, filtering, sorting, admin safeguards |
| `test_request_context.py` | Request ID propagation and sanitisation, error envelope, JSON 500 without leaking details, JSON logs |
| `test_database.py` | Role seeding, constraints (lowercase, unique, FK restrict, cascade), repository filters |
| `test_migrations.py` | Alembic `head` matches the ORM exactly; downgrade to `base` works |
| `test_worker.py` | Celery configuration (JSON only, late acks) and task registration |

Fixtures (`tests/conftest.py`) give each test a fresh database, an app with dependency
overrides (database session, a fake Redis), an `httpx.AsyncClient`, and helpers that create
users and log them in.

## CLI (`cli/tests`, pytest)

```bash
cd cli && pytest
```

HTTP calls go through an `httpx.MockTransport`, so tests need no running server. They cover
config discovery and overrides, `init` safety (no silent overwrite, URL validation), and
`health` output and exit codes for healthy, degraded, unreachable and erroring APIs.

## Frontend (`frontend/src/**/*.test.ts(x)`, Vitest + React Testing Library)

```bash
cd frontend
npm test
npm run test:watch
```

`fetch` is stubbed per test (`src/test/fetchMock.ts`). Tests cover the API client's error
handling and the dashboard's healthy, degraded, unreachable and refresh behaviour, using
accessible queries (roles and names) rather than CSS selectors.

## Principles

- Test behaviour through public interfaces (HTTP, the CLI, rendered UI), not private helpers.
- Every test should fail if the behaviour it names breaks.
- No network access in unit tests. External services are faked at the boundary.
