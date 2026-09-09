import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.metrics import metrics_app, record_http_metrics
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
    allow_headers=["Authorization", "Content-Type"],
)
app.middleware("http")(record_http_metrics)
app.include_router(admin_equipment_router)
app.include_router(admin_reservations_router)
app.include_router(auth_router)
app.include_router(equipment_router)
app.include_router(reservations_router)
app.mount("/metrics", metrics_app)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
