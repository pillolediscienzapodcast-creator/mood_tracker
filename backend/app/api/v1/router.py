from fastapi import APIRouter

from app.api.v1.routes import health, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)
