# Deployment

> DevVault is pre-release. This page covers building images and the settings a
> production-like deployment needs. There is no hardened production setup yet.

## Images

| Image | Build | Notes |
| --- | --- | --- |
| API / worker | `docker build -t devvault-api backend` | Same image; the worker overrides the command with `celery -A app.workers.celery_app worker` |
| Frontend | `docker build --target prod -t devvault-frontend frontend` | nginx serving the built app and proxying `/api/` to `http://api:8000` |

The API image runs as a non-root user and defines a `HEALTHCHECK` against `/api/health`.

## Required configuration

| Variable | Notes |
| --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@host:5432/db`. Use a URL-safe password |
| `REDIS_URL` | `redis://host:6379/0` (use `rediss://` for TLS) |
| `JWT_SECRET` | At least 32 random characters. Changing it invalidates every access token |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | Comma-separated list of allowed browser origins |

Optional settings: `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`,
`DEFAULT_USER_ROLE`, `BOOTSTRAP_ADMIN_EMAIL`, `LOG_LEVEL`, `LOG_JSON`.

## Release steps

1. Run migrations once per release: `alembic upgrade head` (for example as a one-off job).
2. Start API replicas behind a TLS-terminating reverse proxy.
3. Start one or more workers.
4. Point liveness probes at `/api/health` and readiness probes at `/api/health/ready`.

## Vercel (current hosted deployment)

The dashboard and API are deployed together on Vercel:

- `vercel.json` builds `frontend/` as static files and routes `/api/*` to a Python
  serverless function (`api/index.py`) that serves the FastAPI app.
- `requirements.txt` at the repository root lists the function's runtime dependencies
  (no Celery, uvicorn or Alembic).
- PostgreSQL is provided by **Neon** and Redis by **Upstash**, both through the Vercel
  Marketplace. Their variables are prefixed `NEON_` / `UPSTASH_`.

Production environment variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Neon's **unpooled** URL (asyncpg's prepared statements don't mix with pgbouncer). `postgres://` and `sslmode=` are adapted automatically |
| `DATABASE_NULL_POOL` | `true`, so no pooled connections are kept between serverless invocations |
| `REDIS_URL` | Upstash `rediss://` URL |
| `JWT_SECRET` | Random, at least 32 characters (sensitive) |
| `ENVIRONMENT` | `production` |

Pushing to `main` deploys automatically. Run migrations from a trusted machine before
deploying schema changes:

```bash
cd backend
DATABASE_URL="<neon unpooled url>" JWT_SECRET="<any 32+ chars>" alembic upgrade head
```

Limitations on Vercel: the Celery worker does not run there. When background jobs arrive
(Phase 2), the worker will need a container host, or the jobs will need to move to a
serverless queue.

## Not yet done

- Rate limiting on authentication endpoints (planned for Phase 7).
- A production Compose file or Helm chart.
- Serving uvicorn with multiple workers or under gunicorn.
