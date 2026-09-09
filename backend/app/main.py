from fastapi import FastAPI

from backend.app.routes.admin_reservations import router as admin_reservations_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.equipment import router as equipment_router
from backend.app.routes.reservations import router as reservations_router


app = FastAPI(title="Reservoir API")
app.include_router(admin_reservations_router)
app.include_router(auth_router)
app.include_router(equipment_router)
app.include_router(reservations_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
