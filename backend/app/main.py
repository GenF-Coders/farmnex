from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.database import (
    check_database_connection,
    create_tables
)


app = FastAPI(
    title="FarmNex API",
    description="Agricultural marketplace and AI platform",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
    }


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

@app.get("/db", tags=["System"])
async def database_health_check_and_create_tables():
    try:
        await check_database_connection()
        await create_tables()
        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "error",
            "database": "disconnected",
        }


# ============================================================
# READINESS CHECK
# ============================================================

@app.get("/ready", tags=["System"])
async def readiness():
    return {
        "status": "ready",
    }


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    api_router,
    prefix="/api",
)
