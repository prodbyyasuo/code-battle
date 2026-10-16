"""Top-level API router."""

from fastapi import APIRouter

from app.api.auth import auth_router
from app.api.users import users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
