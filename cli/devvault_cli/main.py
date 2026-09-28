"""Entry point for the `devvault` command.

Phase 1 provides `init`, `health` and `version`. Analysis commands arrive in later phases.
"""

from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import httpx
import typer

from devvault_cli import __version__
from devvault_cli.client import ApiError, DevVaultClient
from devvault_cli.config import CONFIG_FILENAME, CliConfig, load_config, render_config

app = typer.Typer(
    name="devvault",
    help="DevVault developer engineering workspace CLI.",
    no_args_is_help=True,
    add_completion=False,
)

# Tests inject an httpx MockTransport here instead of patching internals.
_transport: httpx.BaseTransport | None = None


def _validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise typer.BadParameter("must be an http(s) URL, e.g. http://localhost:8000")
    return value.rstrip("/")


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo(f"devvault {__version__}")


@app.command()
def init(
    directory: Annotated[
        Path, typer.Argument(file_okay=False, help="Project directory to initialise")
    ] = Path("."),
    api_url: Annotated[
        str, typer.Option(callback=_validate_url, help="DevVault API base URL")
    ] = "http://localhost:8000",
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config")] = False,
) -> None:
    """Create a .devvault.toml configuration file in DIRECTORY."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / CONFIG_FILENAME
    if target.exists() and not force:
        typer.echo(f"{target} already exists (use --force to overwrite)", err=True)
        raise typer.Exit(code=1)
    target.write_text(render_config(CliConfig(api_url=api_url)), encoding="utf-8")
    typer.echo(f"Wrote {target}")


@app.command()
def health(
    ready: Annotated[
        bool, typer.Option("--ready", help="Also check database and Redis readiness")
    ] = False,
) -> None:
    """Check that the DevVault API is reachable."""
    config = load_config(Path.cwd())
    try:
        with DevVaultClient(config.api_url, transport=_transport) as client:
            payload = client.health()
            typer.echo(f"API {config.api_url}: {payload.get('status', 'unknown')}")
            if ready:
                readiness = client.readiness()
                for name, status in sorted(readiness.get("checks", {}).items()):
                    typer.echo(f"  {name}: {status}")
                if readiness.get("status") != "ok":
                    raise typer.Exit(code=1)
    except ApiError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
