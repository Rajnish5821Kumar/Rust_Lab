# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Monorepo layout with `backend/`, `frontend/`, `cli/` and `docs/`.
- FastAPI application with `GET /api/health` and `GET /api/health/ready`.
- PostgreSQL configuration using SQLAlchemy 2 (async, asyncpg) and Alembic; initial
  migration creating `roles`, `users` and `refresh_tokens` and seeding the three roles.
- Authentication: registration, login, logout, Argon2id password hashing, short-lived JWT
  access tokens, hashed rotating refresh tokens with reuse detection.
- Role-based access control (`admin`, `developer`, `viewer`); profile, password change and
  admin user management endpoints with pagination, filtering and sorting.
- Consistent error envelope, `X-Request-ID` propagation and structured JSON logging.
- Redis configuration and a Celery worker with a smoke-test task.
- React + TypeScript + Tailwind dashboard shell that shows live API, database and Redis status.
- `devvault` CLI with `init`, `health` and `version` commands.
- Test suites: pytest (backend and CLI) and Vitest + React Testing Library (frontend).
- Docker images for the API/worker and frontend; `docker-compose.yml` for the full stack.
- GitHub Actions for backend, frontend, CLI, security scanning and Docker builds.
- Project documentation and architecture decision records.
