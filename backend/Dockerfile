# syntax=docker/dockerfile:1

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system reservoir \
    && adduser --system --ingroup reservoir reservoir

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt

COPY alembic.ini ./
COPY backend ./backend

RUN chmod +x backend/docker-entrypoint.sh

USER reservoir

EXPOSE 8000

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
