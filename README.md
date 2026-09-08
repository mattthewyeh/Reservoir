# Reservoir

A full-stack platform for reserving shared equipment and preventing conflicting bookings.

## Planned stack

- React and TypeScript
- FastAPI
- PostgreSQL
- SQLAlchemy and Alembic
- Docker
- AWS

## Current status

Initial FastAPI backend setup with an automated health endpoint test and a PostgreSQL development service.

## Run the tests

Install the development dependencies and run pytest from the project root:

```bash
pip install -r backend/requirements-dev.txt
pytest
```

## Run PostgreSQL

Create your local environment file and start the database from the project root:

```bash
cp .env.example .env
docker compose up -d db
docker compose ps
```

Stop the database without deleting its stored data:

```bash
docker compose down
```

## Database migrations

Reservoir uses SQLAlchemy for database access and Alembic for schema migrations.
After changing the database models, generate and apply a migration from the project root:

```bash
alembic revision --autogenerate -m "Describe the schema change"
alembic upgrade head
```
