from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.database import check_database_connection, close_database, create_tables, AsyncSessionLocal
from app.repositories.role_repository import RoleRepository
from app.core.database import (
    AsyncSessionLocal,
    check_database_connection,
    create_tables,
)
from app.repositories.role_repository import RoleRepository


DEFAULT_ROLES = {
    "SUPER_ADMIN": "Platform super administrator",
    "ADMIN": "Platform administrator",
    "MANAGER": "Platform manager",
    "STAFF": "Platform staff",
    "LOGISTICS_MANAGER": "Manages shipments and delivery partners",
    "DELIVERY_AGENT": "Delivers customer orders",
    "SUPPORT": "Customer support staff",
    "VENDOR": "Marketplace vendor",
    "CUSTOMER": "FarmNex customer",
    "FARMER": "FarmNex farmer",
}


async def seed_default_roles() -> None:
    async with AsyncSessionLocal() as session:
        try:
            repository = RoleRepository(session)
            for name, description in DEFAULT_ROLES.items():
                if await repository.get_by_name(name) is None:
                    await repository.create(
                        name=name,
                        description=description,
                    )
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await seed_default_roles()
    yield
    await close_database()


app = FastAPI(
    title="FarmNex API",
    description="Agricultural marketplace and AI platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}


@app.get("/db", tags=["System"])
async def database_health_check():
    try:
        await check_database_connection()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {
            "status": "error",
            "database": "disconnected",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


@app.get("/ready", tags=["System"])
async def readiness():
    return {"status": "ready"}


app.include_router(api_router, prefix="/api")
