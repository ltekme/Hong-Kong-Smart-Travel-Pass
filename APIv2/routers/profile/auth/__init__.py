import time
import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)
from .models import AuthDataModel
from ....dependence import (
    dbSessionDepend,
    userServiceDepend,
    userSessionServiceDepend
)
from ....config import (
    logger,
)

router = APIRouter(prefix="/auth")


@router.get("", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    userService: userServiceDepend,
    userSessionService:  userSessionServiceDepend,
) -> AuthDataModel.Response:
    """Get sessionToken for anonymous user"""
    anonymousUser = userService(dbSession).createAnonymous()
    anonymousUserSession = userSessionService(dbSession).createForUserProfile(anonymousUser)
    logger.info(f"Created session for anonymous user {anonymousUser.username=}")
    dbSession.commit()
    return AuthDataModel.Response(
        sessionToken=anonymousUserSession.sessionToken,
        expireEpoch=int(time.mktime(anonymousUserSession.expire.timetuple())),
        username=anonymousUser.username,
    )


@router.get("/ping", response_model=AuthDataModel.Response)
async def ping(
    dbSession: dbSessionDepend,
    userSessionService: userSessionServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken info for a user"""
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    session = userSessionService(dbSession).updateExpiration(x_SessionToken)
    if session is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    dbSession.commit()
    logger.info(f"Updated session {x_SessionToken[:10]=} for {session.profile.username=}")
    return AuthDataModel.Response(
        sessionToken=x_SessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username="",
    )
