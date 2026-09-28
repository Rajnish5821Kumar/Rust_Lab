# DevVault

DevVault is a developer engineering workspace: one dashboard for analysing software
repositories, tracking engineering activity, monitoring CI/CD, auditing dependencies and
secrets, measuring code quality, and exporting engineering reports. It will work with both
local Git repositories and GitHub.

> **Status: early development (Phase 1 of 7).** The foundation is in place: API,
> database, authentication, background workers, dashboard shell, CLI skeleton, Docker
> and CI. Repository analytics are **not implemented yet**. See the [roadmap](#roadmap).

## What works today

| Area | Status |
| --- | --- |
| `GET /api/health` liveness and `GET /api/health/ready` (PostgreSQL + Redis) readiness | ✅ |
| Registration, login, refresh-token rotation with reuse detection, logout | ✅ |
| Roles (`admin`, `developer`, `viewer`) and role-based access control | ✅ |
| User profile, password change, admin user management (paginated, filterable, sortable) | ✅ |
| Consistent JSON errors, request IDs, structured JSON logs | ✅ |
| PostgreSQL via SQLAlchemy 2 (async) + Alembic migrations | ✅ |
| Celery worker on Redis (smoke-test task only) | ✅ |
| React dashboard showing live API/database/Redis status | ✅ |
| `devvault` CLI: `init`, `health`, `version` | ✅ |
| Git analytics, GitHub sync, issues, PRs, CI, dependencies, secrets, quality, reports | ⏳ planned |

## Repository layout

```
devvault/
├── backend/     FastAPI app, SQLAlchemy models, Alembic migrations, Celery worker, pytest suite
├── frontend/    React + TypeScript + Vite + Tailwind dashboard, Vitest suite
├── cli/         Typer-based `devvault` command, pytest suite
├── docs/        Architecture, API, database, CLI, deployment, testing, security, ADRs
├── .github/     CI workflows and Dependabot
└── docker-compose.yml
```

## Quick start (Docker)

Requires Docker with Compose v2.

```bash
cp .env.example .env
# Fill in POSTGRES_PASSWORD and JWT_SECRET. Generate each with:
python -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up --build
```

Then open:

- Dashboard: http://localhost:5173
- API docs (Swagger UI): http://localhost:8000/api/docs
- Health: http://localhost:8000/api/health → `{"status":"ok","service":"devvault"}`

Compose refuses to start if a required secret is missing; nothing falls back to a
built-in password. To make your first account an admin, set `BOOTSTRAP_ADMIN_EMAIL`
in `.env` before registering it.

## Local development without Docker

See [docs/development.md](docs/development.md). In short:

```bash
# Backend (Python 3.12+)
cd backend && python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                   # runs against in-memory SQLite by default

# Frontend (Node 22.22+ or 24)
cd frontend && npm install && npm test && npm run dev

# CLI
cd cli && pip install -e ".[dev]" && devvault --help
```

## Documentation

- [Architecture](docs/architecture.md) and [decision records](docs/architecture/decisions/)
- [Development setup](docs/development.md)
- [API](docs/api.md)
- [Database](docs/database.md)
- [CLI](docs/cli.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md) and the [security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Roadmap

1. **Foundation**: repository structure, API, database, auth, tests, Docker ← *current*
2. Project and repository management, local Git analyzer, GitHub integration
3. Issue and pull request analytics, CI/CD analytics
4. Dependency analyzer, secret scanner, code quality analyzer
5. Dashboard charts and report export (JSON, CSV, HTML, Markdown)
6. Full CLI (`analyze`, `git`, `github`, `security`, `report`, …)
7. Hardening: advanced testing, performance, rate limiting, audit log

## AI assistance disclosure

This is a personal project. Parts of the code and documentation were written with the help
of an AI coding assistant (Claude, by Anthropic) and reviewed by the author. Commits that
include AI-assisted work carry a `Co-Authored-By` trailer.

## License

[MIT](LICENSE)
