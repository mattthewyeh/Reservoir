from fastapi import FastAPI

from backend.app.routes.equipment import router as equipment_router


app = FastAPI(title="Reservoir API")
app.include_router(equipment_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
