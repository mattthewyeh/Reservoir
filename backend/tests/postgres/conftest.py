import os
import subprocess
import sys
from collections.abc import Callable, Generator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEST_DATABASE_ADMIN_URL = (
    "postgresql+psycopg://reservoir_test:reservoir_test_password"
    "@localhost:5433/postgres"
)


@pytest.fixture
def postgres_database_url() -> Generator[str, None, None]:
    admin_url = os.getenv(
        "TEST_DATABASE_ADMIN_URL",
        DEFAULT_TEST_DATABASE_ADMIN_URL,
    )
    database_name = f"reservoir_test_{uuid4().hex}"
    test_database_url = make_url(admin_url).set(database=database_name)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')

    try:
        yield test_database_url.render_as_string(hide_password=False)
    finally:
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(
                f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'
            )
        admin_engine.dispose()


@pytest.fixture
def run_alembic(
    postgres_database_url: str,
) -> Callable[..., subprocess.CompletedProcess[str]]:
    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["DATABASE_URL"] = postgres_database_url
        return subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

    return run
