import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


load_dotenv()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    component_names = (
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
    )
    components = {name: os.getenv(name) for name in component_names}
    missing_components = [name for name, value in components.items() if not value]

    if missing_components:
        missing = ", ".join(missing_components)
        raise RuntimeError(
            "DATABASE_URL is not configured and database components are missing: "
            f"{missing}"
        )

    return URL.create(
        "postgresql+psycopg",
        username=components["DATABASE_USER"],
        password=components["DATABASE_PASSWORD"],
        host=components["DATABASE_HOST"],
        port=int(components["DATABASE_PORT"]),
        database=components["DATABASE_NAME"],
    ).render_as_string(hide_password=False)


DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
