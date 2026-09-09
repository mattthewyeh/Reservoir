import pytest

from backend.app.database import get_database_url


DATABASE_COMPONENTS = (
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
)


def test_database_url_takes_precedence(monkeypatch: pytest.MonkeyPatch):
    expected_url = "postgresql+psycopg://explicit:secret@database/reservoir"
    monkeypatch.setenv("DATABASE_URL", expected_url)

    assert get_database_url() == expected_url


def test_database_url_can_be_built_from_components(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_HOST", "database.internal")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "reservoir")
    monkeypatch.setenv("DATABASE_USER", "reservoir")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret@password")

    assert get_database_url() == (
        "postgresql+psycopg://reservoir:secret%40password@"
        "database.internal:5432/reservoir"
    )


def test_database_url_reports_missing_components(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for component in DATABASE_COMPONENTS:
        monkeypatch.delenv(component, raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_HOST, DATABASE_PORT"):
        get_database_url()
