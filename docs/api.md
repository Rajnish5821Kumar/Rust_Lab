# API

The API is served under `/api`. FastAPI generates an interactive reference from the code:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

This page covers conventions and gives an overview. The OpenAPI document is the
authoritative reference.

## Conventions

### Authentication

Send the access token as a bearer token:

```
Authorization: Bearer <access_token>
```

Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15). Use the refresh token
to get a new pair. Each refresh token works once: refreshing revokes it and returns a
new one.

### Errors

Every error response uses the same envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [{ "loc": ["body", "password"], "msg": "String should have at least 12 characters", "type": "string_too_short" }],
    "request_id": "5f0c1a3e9b7d4c2a8e6f1b3d5c7a9e0f"
  }
}
```

| Status | `code` | When |
| --- | --- | --- |
| 401 | `authentication_failed` | Missing, invalid or expired credentials |
| 403 | `permission_denied` | Authenticated, but the role is not allowed |
| 404 | `not_found` | Unknown resource or route |
| 409 | `conflict` | Unique field already in use |
| 422 | `validation_error` | Invalid body, query or path parameters |
| 500 | `internal_error` | Unexpected server error (details are logged, not returned) |

### Request IDs

Every response has an `X-Request-ID` header. You can send your own ID (up to 128 characters
from `A-Z a-z 0-9 . _ -`) to correlate logs across services.

### Pagination, filtering and sorting

List endpoints accept `limit` (1–100, default 20) and `offset` (default 0) and return:

```json
{ "items": [...], "total": 42, "limit": 20, "offset": 0 }
```

Sorting uses `sort=<field>` for ascending or `sort=-<field>` for descending. Each endpoint
allows a fixed set of fields, and any other value returns 422.

## Endpoints (Phase 1)

### Health

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/health` | none | Liveness: `{"status": "ok", "service": "devvault"}` |
| GET | `/api/health/ready` | none | Readiness: checks PostgreSQL and Redis. Returns 503 if either is down |

### Auth: `/api/auth`

| Method | Path | Body | Result |
| --- | --- | --- | --- |
| POST | `/register` | `email`, `username`, `password` (12–128 chars), `full_name?` | 201 user |
| POST | `/login` | `email`, `password` | token pair |
| POST | `/refresh` | `refresh_token` | new token pair (old refresh token revoked) |
| POST | `/logout` | `refresh_token` | 204; idempotent |

A token pair is `{access_token, refresh_token, token_type: "bearer", expires_in}`.

### Users: `/api/users`

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/me` | any | Current user's profile |
| PATCH | `/me` | any | Update `username` and/or `full_name` |
| POST | `/me/password` | any | Change password; signs out every session |
| GET | `` (list) | admin | Filters: `role`, `is_active`. Sort: `created_at`, `email`, `username` |
| PATCH | `/{user_id}` | admin | Set `role` and/or `is_active`. Admins cannot demote or deactivate themselves |

## Example

```bash
curl -s -X POST localhost:8000/api/auth/register -H 'content-type: application/json' \
  -d '{"email":"me@example.com","username":"me","password":"a-long-passphrase"}'

TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"a-long-passphrase"}' | jq -r .access_token)

curl -s localhost:8000/api/users/me -H "Authorization: Bearer $TOKEN"
```
