import time
import typing as t
from fastapi import (
    APIRouter,
    Header
)
from .models import AuthDataModel
from ....dependence import (
    dbSessionDepend,
    getUserServiceDepend,
    getUserSessionServiceDepend
)
from ....config import (
    logger,
)

router = APIRouter(prefix="/auth")


@router.get("", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    getUserService: getUserServiceDepend,
    getUserSessionService:  getUserSessionServiceDepend,
) -> AuthDataModel.Response:
    """Get sessionToken for anonymous user"""
    anonymousUser = getUserService(dbSession).createAnonymous()
    anonymousUserSession = getUserSessionService(dbSession).createForUser(anonymousUser)
    dbSession.commit()
    logger.info(f"Created session for anonymous user {anonymousUser.id=}")
    return AuthDataModel.Response(
        sessionToken=anonymousUserSession.sessionToken,
        expireEpoch=int(time.mktime(anonymousUserSession.expire.timetuple())),
        username=anonymousUser.username,
    )


@router.get("/ping", response_model=AuthDataModel.Response)
async def ping(
    dbSession: dbSessionDepend,
    getUserSessionService:  getUserSessionServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken info for a user"""
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    dbSession.commit()
    logger.info(f"Updated session {session.sessionToken[:10]=} for {session.user.username=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username=session.user.username,
    )
