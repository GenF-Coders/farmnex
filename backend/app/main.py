from fastapi import FastAPI

app = FastAPI(
    title="FarmNex API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "FarmNex API is running",
        "status": "healthy"
    }

@app.get("/health")
def health():
    return {"status": "ok"}