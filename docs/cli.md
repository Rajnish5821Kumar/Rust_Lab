# CLI

The `devvault` command lives in `cli/` and talks to the DevVault API over HTTP.

```bash
cd cli
pip install -e .
devvault --help
```

## Configuration

`devvault init` writes a `.devvault.toml` in the project directory:

```toml
[api]
url = "http://localhost:8000"
```

The CLI looks for this file in the current directory and then in each parent directory.
The `DEVVAULT_API_URL` environment variable overrides it. Don't store tokens in this file.
When authenticated commands arrive, credentials will come from environment variables.

## Commands available now

| Command | Description |
| --- | --- |
| `devvault version` | Print the CLI version |
| `devvault init [DIR] [--api-url URL] [--force]` | Create `.devvault.toml`. Refuses to overwrite unless `--force` is given |
| `devvault health [--ready]` | Check the API. `--ready` also reports PostgreSQL and Redis; the exit code is 1 if anything is down |

## Planned commands

`project`, `repo`, `analyze`, `git`, `github`, `issues`, `prs`, `ci`, `dependencies`,
`security` and `report` arrive in later phases (see the roadmap in the README).
For example, `devvault analyze ./my-project` is planned for Phase 6, once the Git
analyzer exists.
