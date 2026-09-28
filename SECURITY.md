# Security Policy

## Supported versions

DevVault has not had a stable release yet. Security fixes are applied to the `main` branch.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Report them privately through
GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on the repository (Security tab → "Report a vulnerability").

Include:

- the affected component (API, worker, frontend, CLI) and version or commit
- steps to reproduce, or a proof of concept
- the impact as you understand it

You can expect an acknowledgement within 7 days. As a personal project, fix timelines
depend on severity and maintainer availability.

## Handling secrets

- Never commit `.env` files, tokens, passwords or private keys. `.env` is git-ignored.
- CI runs [gitleaks](https://github.com/gitleaks/gitleaks) on every push and pull request.
- If a secret is committed by accident, **rotate it first**. Removing it from history
  does not make it safe again.

See [docs/security.md](docs/security.md) for the security design of the application itself.
