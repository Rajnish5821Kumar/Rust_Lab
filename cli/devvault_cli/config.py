"""Project-local CLI configuration stored in `.devvault.toml`.

Only non-secret settings live in this file. Tokens are read from environment variables
so they never end up committed alongside a project.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAME = ".devvault.toml"
DEFAULT_API_URL = "http://localhost:8000"
API_URL_ENV = "DEVVAULT_API_URL"


@dataclass(frozen=True, slots=True)
class CliConfig:
    api_url: str = DEFAULT_API_URL


def find_config(start: Path) -> Path | None:
    """Return the nearest `.devvault.toml` in `start` or its parents."""
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_config(start: Path) -> CliConfig:
    api_url = DEFAULT_API_URL
    path = find_config(start)
    if path is not None:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        api_url = str(data.get("api", {}).get("url", api_url))
    # The environment always wins so CI can point at a different server.
    api_url = os.environ.get(API_URL_ENV, api_url)
    return CliConfig(api_url=api_url.rstrip("/"))


def render_config(config: CliConfig) -> str:
    # Written by hand to avoid a TOML-writer dependency; values are validated URLs.
    return (
        "# DevVault CLI configuration. Do not store tokens here; use environment variables.\n"
        "[api]\n"
        f'url = "{config.api_url}"\n'
    )
