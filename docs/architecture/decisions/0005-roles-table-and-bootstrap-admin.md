# 5. Roles as a table; admin bootstrapped by configuration

- Status: Accepted
- Date: 2026-09-28

## Context

DevVault needs `admin`, `developer` and `viewer` roles. The very first admin has to come
from somewhere, and the project must not ship default credentials.

## Decision

- Roles are rows in a `roles` table, seeded by the initial migration. Each user has one
  role through `users.role_id` (`ON DELETE RESTRICT`).
- New registrations get `DEFAULT_USER_ROLE` (default `viewer`, least privilege).
- If `BOOTSTRAP_ADMIN_EMAIL` is set, registering with that exact email creates an admin.
  After that, admins promote other users through `PATCH /api/users/{id}`.
- Admins cannot demote or deactivate their own account.

Project-level membership roles (for example "maintainer of project X") are a separate
concern and will be modelled with `ProjectMember` in Phase 2.

## Consequences

- No credentials exist in code or images.
- The operator must set `BOOTSTRAP_ADMIN_EMAIL` before registering the first account.
  Registering first and setting it afterwards has no effect on the existing account.
- Adding a role requires a migration, which is intentional because it changes authorization.
