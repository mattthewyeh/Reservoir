import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from backend.app.database import check_database_connection
from backend.app.metrics import metrics_app, record_http_metrics
from backend.app.observability import log_http_request
from backend.app.routes.admin_equipment import router as admin_equipment_router
from backend.app.routes.admin_reservations import router as admin_reservations_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.equipment import router as equipment_router
from backend.app.routes.reservations import router as reservations_router


app = FastAPI(
    title="Reservoir API",
    root_path=os.getenv("ROOT_PATH", ""),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.middleware("http")(record_http_metrics)
app.middleware("http")(log_http_request)
app.include_router(admin_equipment_router)
app.include_router(admin_reservations_router)
app.include_router(auth_router)
app.include_router(equipment_router)
app.include_router(reservations_router)
app.mount("/metrics", metrics_app)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/ready", include_in_schema=False)
def readiness_check():
    try:
        check_database_connection()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from None

    return {"status": "ready"}
