import typing as t

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .routers import chatLLM
from .routers import googleServices
from .routers import profile
from .modules.exception import NotAuthorizedError
from .modules.exception import InsufficientQoutaError
from .modules.exception import AuthorizationError
from .modules.exception import ChatLLMServiceError

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


@app.exception_handler(AuthorizationError)
async def handleAuthorizationError(request: Request, exeception: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": "Authorization Failed"},
    )


@app.exception_handler(RequestValidationError)
async def handleValidationError(request: Request, exeception: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Mailformed Request"},
    )


@app.exception_handler(NotAuthorizedError)
async def handlePermissionError(request: Request, exeception: NotAuthorizedError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": f"You do not have permission to perform \"{exeception.action}\""},
    )


@app.exception_handler(InsufficientQoutaError)
async def handleQuotaExceededError(request: Request, exeception: InsufficientQoutaError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": "Quota Exceeded"},
    )


@app.exception_handler(ChatLLMServiceError)
async def handleChatLLMServiceError(request: Request, exeception: ChatLLMServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "There is an error processing your request" if not exeception.args else exeception.args[0]},
    )
