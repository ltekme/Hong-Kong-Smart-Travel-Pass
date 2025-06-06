import typing as t
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    chatLLM,
    googleServices,
    profile,
)


app = FastAPI(root_path="/api/v2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chatLLM.router)
app.include_router(googleServices.router)
app.include_router(profile.router)


@app.exception_handler(500)
async def handleError(request: Request, exeception: t.Any) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Server Error"},
    )


@app.exception_handler(404)
async def handleNotFound(request: Request, exeception: t.Any) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Content Not Avalable"},
    )


@app.exception_handler(RequestValidationError)
async def handleValidationError(request: Request, exeception: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Mailformed Request"},
    )


@app.exception_handler(PermissionError)
async def handlePermissionError(request: Request, exeception: PermissionError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": "Permission Denied"},
    )
