from alembic.config import (
    Config,
    command
)
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException
from .routers import (
    chat,
    googleServices,
    profile,
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
app.include_router(profile.router)


@app.exception_handler(500)
@app.exception_handler(404)
async def handleError(request: Request, exeception: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exeception.status_code,
        headers={
            "X-Error": "Nope" if exeception.status_code == 404 else "I'm a teapot",
        },
        content={"detail": "Hello World! :-]"},
    )


@app.exception_handler(RequestValidationError)
async def handleValidationError(request: Request, exeception: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        headers={
            "X-Error": "Invalid Request"
        },
        content={"detail": "Hello World! :-]"},
    )
