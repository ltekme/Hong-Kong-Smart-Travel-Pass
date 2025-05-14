from fastapi import APIRouter
from . import summory, auth

router = APIRouter(prefix="/profile")
router.include_router(summory.router)
router.include_router(auth.router)
