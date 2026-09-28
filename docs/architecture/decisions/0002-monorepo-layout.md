# 2. Single repository with backend, frontend and CLI packages

- Status: Accepted
- Date: 2026-09-28

## Context

DevVault has three deliverables: an API with background workers, a web dashboard, and a
CLI. They change together often. For example, a new API endpoint usually needs a UI
view and a CLI command.

## Decision

Keep all three in one repository as independent packages: `backend/`, `frontend/` and
`cli/`. Each has its own dependency manifest, tooling configuration and test suite. The
API and the Celery worker share the `backend` package and Docker image.

The CLI is a separate Python package that talks to the API over HTTP. It does not import
backend code, so it stays lightweight to install and cannot bypass API authorization.

## Consequences

- One pull request can change the API contract and its consumers together.
- CI workflows are scoped by path, so a frontend-only change doesn't run backend tests.
- The CLI cannot reuse backend Pydantic schemas directly. If duplication grows, a shared
  OpenAPI-generated client can be introduced.
