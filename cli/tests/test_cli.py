import json
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from devvault_cli import main
from devvault_cli.config import CONFIG_FILENAME, load_config

runner = CliRunner()

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def mock_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[Handler], list[str]]]:
    """Route CLI HTTP calls to a handler; returns the list of requested URLs."""

    def install(handler: Handler) -> list[str]:
        seen: list[str] = []

        def recording(request: httpx.Request) -> httpx.Response:
            seen.append(str(request.url))
            return handler(request)

        monkeypatch.setattr(main, "_transport", httpx.MockTransport(recording))
        return seen

    yield install


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEVVAULT_API_URL", raising=False)
    return tmp_path


def test_version() -> None:
    result = runner.invoke(main.app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "devvault 0.1.0"


def test_init_writes_config(isolated_cwd: Path) -> None:
    result = runner.invoke(main.app, ["init", "--api-url", "https://devvault.example.com/"])

    assert result.exit_code == 0
    assert load_config(isolated_cwd).api_url == "https://devvault.example.com"


def test_init_refuses_to_overwrite_without_force(isolated_cwd: Path) -> None:
    (isolated_cwd / CONFIG_FILENAME).write_text("# keep me\n", encoding="utf-8")

    result = runner.invoke(main.app, ["init"])

    assert result.exit_code == 1
    assert (isolated_cwd / CONFIG_FILENAME).read_text(encoding="utf-8") == "# keep me\n"


def test_init_force_overwrites(isolated_cwd: Path) -> None:
    (isolated_cwd / CONFIG_FILENAME).write_text("# old\n", encoding="utf-8")

    result = runner.invoke(main.app, ["init", "--force"])

    assert result.exit_code == 0
    assert "[api]" in (isolated_cwd / CONFIG_FILENAME).read_text(encoding="utf-8")


def test_init_rejects_non_http_url() -> None:
    result = runner.invoke(main.app, ["init", "--api-url", "file:///etc/passwd"])

    assert result.exit_code != 0
    assert not Path(CONFIG_FILENAME).exists()


def test_config_is_found_in_parent_directory(isolated_cwd: Path) -> None:
    runner.invoke(main.app, ["init", "--api-url", "http://parent.test:9000"])
    nested = isolated_cwd / "a" / "b"
    nested.mkdir(parents=True)

    assert load_config(nested).api_url == "http://parent.test:9000"


def test_env_var_overrides_config(isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(main.app, ["init", "--api-url", "http://file.test"])
    monkeypatch.setenv("DEVVAULT_API_URL", "http://env.test/")

    assert load_config(isolated_cwd).api_url == "http://env.test"


def test_health_reports_ok(mock_api: Callable[[Handler], list[str]]) -> None:
    seen = mock_api(lambda _: httpx.Response(200, json={"status": "ok", "service": "devvault"}))

    result = runner.invoke(main.app, ["health"])

    assert result.exit_code == 0
    assert "API http://localhost:8000: ok" in result.stdout
    assert seen == ["http://localhost:8000/api/health"]


def test_health_ready_fails_when_dependency_down(
    mock_api: Callable[[Handler], list[str]],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/health/ready":
            body = {"status": "error", "checks": {"database": "ok", "redis": "error"}}
            return httpx.Response(503, content=json.dumps(body))
        return httpx.Response(200, json={"status": "ok", "service": "devvault"})

    mock_api(handler)

    result = runner.invoke(main.app, ["health", "--ready"])

    assert result.exit_code == 1
    assert "redis: error" in result.stdout
    assert "database: ok" in result.stdout


def test_health_handles_unreachable_api(mock_api: Callable[[Handler], list[str]]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    mock_api(handler)

    result = runner.invoke(main.app, ["health"])

    assert result.exit_code == 1
    assert "Could not reach" in result.stderr


def test_health_handles_server_error(mock_api: Callable[[Handler], list[str]]) -> None:
    mock_api(lambda _: httpx.Response(500, json={"error": {}}))

    result = runner.invoke(main.app, ["health"])

    assert result.exit_code == 1
    assert "HTTP 500" in result.stderr
