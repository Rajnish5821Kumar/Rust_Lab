# Security design

This page describes how DevVault protects accounts and data. To report a vulnerability,
see [SECURITY.md](../SECURITY.md).

## Passwords

- Hashed with **Argon2id** (`argon2-cffi` defaults). Hashes are upgraded automatically at
  login if the parameters change.
- Length between 12 and 128 characters. Length-based rules follow NIST SP 800-63B guidance.
- Logins for unknown emails still run a hash verification, so response timing does not
  reveal which accounts exist. Wrong-email and wrong-password failures return the same message.
- Changing a password revokes every refresh token for the account.

## Tokens

- **Access tokens** are HS256 JWTs that live 15 minutes by default. They contain only
  `sub`, `type`, `iss`, `iat`, `exp` and `jti`. The role is **not** in the token: the user
  is loaded on every request, so deactivation and role changes apply immediately.
  Decoding pins the algorithm, which rejects `alg: none` and algorithm-confusion tokens,
  and requires every claim.
- **Refresh tokens** are 48 random bytes (URL-safe). Only their SHA-256 digest is stored.
  They expire after 7 days by default.
- **Rotation with reuse detection.** Each refresh revokes the presented token and issues a
  new one. If a revoked token is presented again, every session for that user is revoked,
  on the assumption that the token was stolen.
- Logout revokes the refresh token. An access token already issued stays valid until
  it expires.

## Authorization

- Roles: `admin`, `developer`, `viewer`. New users get `DEFAULT_USER_ROLE` (default `viewer`).
- Endpoints declare the roles they allow with the `require_roles(...)` dependency.
- There are no default admin credentials. An account becomes admin only through
  `BOOTSTRAP_ADMIN_EMAIL` at registration or promotion by an existing admin.
- Admins cannot demote or deactivate themselves, which prevents accidental lock-out.

## Input and output handling

- Pydantic validates every request body and query parameter. Sort fields come from an
  allow-list.
- Database access goes through SQLAlchemy expressions, which are always parameterised.
- Validation errors never echo submitted values. Unhandled exceptions return a generic
  500 with a request ID, and the details go only to the server log.
- Caller-supplied `X-Request-ID` values are accepted only if they match a strict
  pattern, which prevents log injection.

## Configuration and secrets

- Secrets come only from environment variables. `.env` is git-ignored, and Compose refuses
  to start without `POSTGRES_PASSWORD` and `JWT_SECRET`.
- `JWT_SECRET` must be at least 32 characters and is a `SecretStr`, so it never appears
  in logs or `repr` output.
- Local Postgres and Redis ports are published on `127.0.0.1` only.

## Supply chain and CI

- `pip-audit` and `npm audit` check dependencies for known vulnerabilities, Bandit runs
  static analysis, and gitleaks scans the Git history for committed secrets.
- Dependabot keeps dependencies, GitHub Actions and base images up to date.
- Workflows use read-only `GITHUB_TOKEN` permissions and contain no secrets.

## Planned hardening

- Rate limiting on login, registration and refresh (Redis-backed).
- Audit log with privacy-preserving client identifiers (a salted hash of the IP).
- Safe subprocess execution for the Git analyzer (argument lists, no shell, timeouts).
- Secret redaction in scanner output.
