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
)
from ....config import (
    logger,
)
from ....modules import UserService

router = APIRouter(prefix="/auth")


@router.get("", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken for a user"""
    if x_FacebookAccessToken is None:
        # Anonymous User
        anonymousUser = UserService.createAnonymousUser(dbSession=dbSession)
        anonymousUserSession = UserService.createUserSession(
            userProfile=anonymousUser,
            expire=UserService.createSessionTokenExpireDatetime(),
            dbSession=dbSession,
        )
        return AuthDataModel.Response(
            sessionToken=anonymousUserSession.sessionToken,
            expireEpoch=int(time.mktime(anonymousUserSession.expire.timetuple())),
            username=anonymousUser.username,
        )

    try:
        user = UserService.getUserProfileFromFacebookAccessToken(
            accessToken=x_FacebookAccessToken,
            dbSession=dbSession,
        )
    except UserService.FacebookUserIdentifyExeception as e:
        logger.warning(e)
        raise HTTPException(
            status_code=400,
            detail=e
        )
    logger.info(f"Removing existing session for {user.id=}")
    UserService.clearExpiredUserSession(
        userProfile=user,
        dbSession=dbSession,
    )
    logger.info(f"Creating session for {x_FacebookAccessToken[:10]=}")
    session = UserService.createUserSession(
        userProfile=user,
        expire=UserService.createSessionTokenExpireDatetime(),
        dbSession=dbSession
    )
    logger.info(f"created session for {x_FacebookAccessToken[:10]=}, {session.sessionToken[:10]=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username=user.username,
    )


@router.get("/ping", response_model=AuthDataModel.Response)
async def ping(
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken info for a user"""
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    session = UserService.updateSessionTokenExpiration(
        sessionToken=x_SessionToken,
        dbSession=dbSession,
    )
    if session is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    return AuthDataModel.Response(
        sessionToken=x_SessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username="",
    )
