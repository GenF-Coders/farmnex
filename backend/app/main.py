from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


app = FastAPI(
    title="FarmNex API",
    description="Agricultural marketplace and AI platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        # Add production frontend URL later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}


@app.get("/ready", tags=["System"])
async def readiness():
    return {"status": "ready"}


app.include_router(api_router)