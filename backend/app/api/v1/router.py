from fastapi import APIRouter

from app.api.v1.routes import health, mood, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    mood.router,
    prefix="/users",
    tags=["Mood"],
)
