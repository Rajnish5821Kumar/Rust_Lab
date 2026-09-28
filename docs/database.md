# Database

DevVault uses PostgreSQL 17 through SQLAlchemy 2's asyncio API and the `asyncpg` driver.
The schema is managed only by Alembic migrations in `backend/alembic/versions/`.

## Current schema (Phase 1)

```
roles                    users                               refresh_tokens
─────────────            ───────────────────────────         ──────────────────────────
id          PK           id              PK                  id          PK
name        UNIQUE       email           UNIQUE, lowercase   user_id     FK → users.id (CASCADE), indexed
description              username        UNIQUE, lowercase   token_hash  UNIQUE (SHA-256 hex)
                         full_name                           expires_at
                         hashed_password (Argon2id)          revoked_at
                         is_active                           created_at
                         role_id         FK → roles.id (RESTRICT), indexed
                         last_login_at
                         created_at / updated_at
```

- Roles are seeded by the first migration: `admin`, `developer`, `viewer`.
- `CHECK` constraints enforce lowercase emails and usernames, so uniqueness is
  effectively case-insensitive.
- A role cannot be deleted while users still have it (`ON DELETE RESTRICT`).
- Deleting a user deletes their refresh tokens (`ON DELETE CASCADE`).
- All timestamps are `timestamptz` and stored in UTC.
- Constraints and indexes follow a naming convention (`backend/app/db/base.py`), so
  migrations produce the same names on every database.

Models planned for later phases (Project, Repository, Commit, Issue, PullRequest,
WorkflowRun, Dependency, SecurityFinding, TestRun, Metric, AuditLog, …) will be added
alongside the features that use them.

## Migrations

```bash
cd backend
alembic upgrade head                                   # apply
alembic revision --autogenerate -m "add projects"      # create; always review the output
alembic downgrade -1                                   # roll back one step
alembic check                                          # fail if models and migrations differ
```

`tests/test_migrations.py` upgrades an empty database to `head` and asserts that the
result matches the ORM metadata exactly. It then checks that downgrading to `base` removes
everything. CI also runs `upgrade`, `check` and `downgrade` against real PostgreSQL.

## Conventions

- **Transactions.** Services commit explicitly, and a failed request rolls back.
  Operations that must not race, such as refresh-token rotation, use `SELECT … FOR UPDATE`.
- **No N+1 queries.** Relationships needed on hot paths are eager-loaded. For example,
  `User.role` uses a joined load, so fetching the current user is a single query.
- **Parameterised SQL only.** Queries go through SQLAlchemy expressions; user input is
  never interpolated into SQL strings.
- **Pagination.** List queries always apply `LIMIT`/`OFFSET` with a deterministic order
  (the requested column, then `id`).
