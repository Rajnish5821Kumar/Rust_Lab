# Contributing to DevVault

DevVault is a personal project, but issues and pull requests are welcome. This guide
explains how to get set up and what a change needs before it can be merged.

## Getting set up

Follow [docs/development.md](docs/development.md) to run the backend, frontend and CLI
locally, or use `docker compose up` for the full stack.

## Before opening a pull request

Run the checks for every part you touched. CI runs the same commands.

```bash
# backend/
ruff check . && ruff format --check . && mypy && pytest

# cli/
ruff check . && ruff format --check . && mypy && pytest

# frontend/
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
```

If you change a SQLAlchemy model, add an Alembic migration
(`alembic revision --autogenerate -m "..."`), review the generated file by hand, and make
sure `tests/test_migrations.py` still passes.

## Guidelines

- **Tests test behaviour.** Add tests that would fail if the feature broke. Don't add tests
  that only exist to raise coverage.
- **Keep modules small and layered.** Routers handle HTTP, services hold business rules,
  repositories hold queries, schemas define the API contract. See
  [docs/architecture.md](docs/architecture.md).
- **Type everything.** Backend and CLI run `mypy --strict`; the frontend uses strict
  TypeScript.
- **No secrets in code, tests, fixtures or workflows.** Configuration comes from environment
  variables.
- **Never run user-provided shell commands.** When a subprocess is unavoidable (for example
  `git`), pass an argument list, never a shell string.
- **Record significant design decisions** as an ADR in
  [docs/architecture/decisions/](docs/architecture/decisions/).

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth): implement refresh token rotation
fix(api): return 404 for unknown users
test(git): add commit parser coverage
docs(api): document repository endpoints
```

One logical change per commit. Don't rewrite published history.

## AI-assisted contributions

If you used an AI tool to write part of a change, say so in the pull request description
and add a `Co-Authored-By` trailer to the commit. You are responsible for reviewing and
understanding everything you submit.
