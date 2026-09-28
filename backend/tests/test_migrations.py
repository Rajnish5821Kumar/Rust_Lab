"""Checks that Alembic migrations produce exactly the schema the ORM models describe."""

from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, select, text

from alembic import command
from app.db.base import Base
from app.db.seed import DEFAULT_ROLES

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def alembic_config(tmp_path: Path) -> tuple[Config, str]:
    db_file = tmp_path / "migrations.db"
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file.as_posix()}")
    config.attributes["configure_logger"] = False
    return config, f"sqlite:///{db_file.as_posix()}"


def test_upgrade_head_matches_models(alembic_config: tuple[Config, str]) -> None:
    config, sync_url = alembic_config

    command.upgrade(config, "head")

    engine = create_engine(sync_url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        roles = set(conn.scalars(select(text("name")).select_from(text("roles"))).all())
    engine.dispose()
    assert diff == []
    assert roles == set(DEFAULT_ROLES)


def test_downgrade_to_base_removes_tables(alembic_config: tuple[Config, str]) -> None:
    config, sync_url = alembic_config

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(sync_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert tables == {"alembic_version"}
