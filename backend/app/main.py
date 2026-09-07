from fastapi import FastAPI

app = FastAPI(title="Reservoir API")

@app.get("/health")
def health_check():
    return {"status": "healthy"}