from fastapi import APIRouter

from app.api.v1.routes.parts import router as parts_router
from app.api.v1.routes.quotes import router as quotes_router


api_router = APIRouter()
api_router.include_router(parts_router, prefix="/parts", tags=["parts"])
api_router.include_router(quotes_router, prefix="/quotes", tags=["quotes"])
