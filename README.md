# Reservoir

A full-stack platform for reserving shared equipment and preventing conflicting bookings.

## Stack

- React and TypeScript
- FastAPI
- PostgreSQL
- SQLAlchemy and Alembic
- Docker
- AWS

## Current status

Containerized React and TypeScript frontend with registration, login, equipment availability and booking, personal reservation management, and administrator inventory and reservation screens. Nginx serves the frontend and proxies the FastAPI API, which uses PostgreSQL and includes isolated API and PostgreSQL integration tests.

## Run the application

Create the environment file, replace the example `JWT_SECRET`, and start the complete application from the project root:

```bash
cp .env.example .env
docker compose up --build -d --wait
```

Open `http://localhost:8080`. API documentation is available at `http://localhost:8080/api/docs`. The API container applies pending Alembic migrations before it starts, and Nginx forwards browser requests from `/api` to the internal API service.

View service status and logs or stop the application with:

```bash
docker compose ps
docker compose logs -f
docker compose down
```

`docker compose down` keeps the PostgreSQL volume. Add `--volumes` only when you intentionally want to delete local database data.

## Local development

To run the backend and frontend directly for hot reloading, first start only PostgreSQL:

```bash
docker compose up -d db
uvicorn backend.app.main:app --reload
```

In another terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. The development frontend connects to `http://localhost:8000` by default. Use `VITE_API_URL` to change the API address, `FRONTEND_ORIGINS` to configure the backend's comma-separated browser origins, and `APP_PORT` to change the containerized application's host port.

## Run the tests

Install the development dependencies and run pytest from the project root:

```bash
pip install -r backend/requirements-dev.txt
pytest
```

The default suite uses in-memory SQLite and excludes tests marked `postgres`. Run the isolated PostgreSQL suite with:

```bash
docker compose --profile test up -d --wait db-test
pytest -m postgres
docker compose --profile test rm -sf db-test
```

Each PostgreSQL test creates a uniquely named database, applies migrations, and deletes the database afterward. The test service stores its database cluster in temporary memory instead of the development volume.

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
- `GET /equipment/availability?starts_at=...&ends_at=...` lists active equipment available for a timezone-aware interval.
- `GET /equipment/{equipment_id}` retrieves one active equipment item.
- `POST /equipment` lets an admin create equipment.
- `PATCH /equipment/{equipment_id}` lets an admin edit, activate, or deactivate equipment.

## Admin equipment API

- `GET /admin/equipment` lets an admin list all equipment, including inactive items.

## Authentication API

Set `JWT_SECRET` in `.env` to a long random value before using authentication.

- `POST /auth/register` creates a regular user account.
- `POST /auth/token` accepts an email in the OAuth2 `username` field and returns a bearer token.
- `GET /auth/me` returns the user identified by a valid bearer token.

## Reservation API

- `GET /reservations` lists the authenticated user's reservations chronologically.
- `GET /reservations/{reservation_id}` retrieves one reservation owned by the authenticated user.
- `POST /reservations` lets an authenticated user reserve active equipment.
- `POST /reservations/{reservation_id}/cancel` cancels an owned reservation that has not started.
- Reservation timestamps must include a timezone and the end must be after the start.
- Reservation ownership always comes from the bearer token, never from client input.
- Confirmed reservations for the same equipment cannot overlap.
- Back-to-back reservations are allowed, and cancelled reservations do not block time.

## Admin reservation API

- `GET /admin/reservations` lists reservations across all users.
- `GET /admin/reservations/{reservation_id}` retrieves any reservation.
- `POST /admin/reservations/{reservation_id}/cancel` lets an admin cancel any confirmed reservation.

## Frontend

- Registration automatically signs the new user in.
- Saved bearer tokens restore a session after a page reload.
- Members can check a local-time window, reserve available equipment, review their reservations, and cancel future bookings.
- Administrators can create, edit, activate, and deactivate equipment and review or cancel reservations across all users.
- Run `npm run lint`, `npm test`, and `npm run build` from `frontend` to validate the UI.

## Admin setup

Register the user normally, then promote the account from the project root:

```bash
python -m backend.app.commands.promote_admin admin@example.com
```

Admin promotion is available only through this local command, not through a public API endpoint.

When the complete application is running in Docker, use:

```bash
docker compose exec api python -m backend.app.commands.promote_admin admin@example.com
```
