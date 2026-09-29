"""Integrated FarmNex entrypoint preserving legacy files."""
import app.domain_model_registry  # noqa: F401
from app.main import app
from app.api.v2.domain_router import router as domain_router
app.include_router(domain_router, prefix="/api/v2")
