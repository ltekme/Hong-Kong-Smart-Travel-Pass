from alembic.config import (
    Config,
    command
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import (
    chat,
    googleServices,
)
from .dependence import dbEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # moved to alembic for migration
    cfg = Config("./alembic.ini")
    with dbEngine.begin() as connection:
        cfg.attributes['connection'] = connection
        command.upgrade(cfg, "head")
    yield
    print('bye')


app = FastAPI(root_path="/api/v2", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router)
app.include_router(googleServices.router)
