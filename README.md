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

Initial FastAPI backend with PostgreSQL, user authentication, and admin-managed equipment.

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

## Data model

- A user can have many reservations and has either a `user` or `admin` role.
- An equipment item can have many reservations over time.
- A reservation belongs to one user and one equipment item.
- Every reservation must end after it starts.

## Equipment API

- `GET /equipment` lists active equipment in name order.
- `GET /equipment/{equipment_id}` retrieves one active equipment item.
- `POST /equipment` lets an admin create equipment.
- `PATCH /equipment/{equipment_id}` lets an admin edit, activate, or deactivate equipment.

## Authentication API

Set `JWT_SECRET` in `.env` to a long random value before using authentication.

- `POST /auth/register` creates a regular user account.
- `POST /auth/token` accepts an email in the OAuth2 `username` field and returns a bearer token.
- `GET /auth/me` returns the user identified by a valid bearer token.

## Reservation API

- `POST /reservations` lets an authenticated user reserve active equipment.
- Reservation timestamps must include a timezone and the end must be after the start.
- Reservation ownership always comes from the bearer token, never from client input.
- Overlapping reservations are not rejected yet; conflict prevention is the next milestone.

## Admin setup

Register the user normally, then promote the account from the project root:

```bash
python -m backend.app.commands.promote_admin admin@example.com
```

Admin promotion is available only through this local command, not through a public API endpoint.
