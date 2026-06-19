"""
Root API router.

Add new domain routers here with their prefix.
All routes are mounted under /api/v1 in application.py.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.auth.api.routes import router as auth_router
from backend.app.example_domain.api.routes import router as example_router

api_router = APIRouter()


@api_router.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


# --- Domain routers ---
api_router.include_router(auth_router)
api_router.include_router(example_router)

# Add new domains here:
# api_router.include_router(users_router, prefix="/users")
# api_router.include_router(reports_router, prefix="/reports")
