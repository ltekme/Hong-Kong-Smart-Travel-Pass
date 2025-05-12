import typing as t
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
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
@app.exception_handler(404)
async def handleError(request: Request, exeception: t.Any) -> JSONResponse:
    if isinstance(exeception, StarletteHTTPException):
        statusCode = exeception.status_code
    else:
        statusCode = 418
    return JSONResponse(
        status_code=statusCode,
        headers={
            "X-Error": "Nope" if statusCode == 404 else "I'm a teapot",
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
