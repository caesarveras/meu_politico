from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.public import router as public_router
from app.routers.sync import router as sync_router

api_router = APIRouter()
api_router.include_router(public_router)
api_router.include_router(auth_router)
api_router.include_router(sync_router)
