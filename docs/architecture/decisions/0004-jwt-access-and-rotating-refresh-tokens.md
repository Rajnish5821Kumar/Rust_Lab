# 4. Short-lived JWT access tokens with rotating, server-side refresh tokens

- Status: Accepted
- Date: 2026-09-28

## Context

The API is used by the browser dashboard and by the CLI. It needs stateless request
authentication, but also real logout and a way to cut off stolen credentials.

## Decision

- **Access token:** HS256 JWT, 15-minute default lifetime, with claims
  `sub, type, iss, iat, exp, jti`. It is validated without a database lookup of the token
  itself. The user row is still loaded on every request, so deactivation and role changes
  take effect immediately. The role is deliberately not a claim.
- **Refresh token:** an opaque random string, not a JWT. Its SHA-256 digest is stored in
  `refresh_tokens` with an expiry and a `revoked_at` timestamp.
- **Rotation:** every refresh revokes the presented token and issues a new pair.
- **Reuse detection:** presenting a revoked refresh token revokes all of that user's
  refresh tokens.
- Tokens travel in JSON bodies and the `Authorization` header. How the browser stores them
  (memory plus an httpOnly cookie, or not) will be decided when the login UI is built.

## Consequences

- Logout and password changes reliably end sessions within one access-token lifetime.
- A database leak does not expose usable refresh tokens.
- Every refresh is a write, which is acceptable at this scale.
- Access tokens cannot be revoked before they expire. If that becomes necessary, a
  `jti` denylist in Redis can be added.
