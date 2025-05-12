import time
import datetime
import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)
from . import summory
from ..profile.models import AuthDataModel
from ...dependence import (
    dbSessionDepend,
)
from ...config import (
    logger,
    settings,
)
from ...modules import UserService


router = APIRouter(prefix="/profile")
router.include_router(summory.router)


@router.get("/auth", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken for a user"""
    currentDatetime = datetime.datetime.now(datetime.UTC)
    timeDelta = datetime.timedelta(seconds=settings.userSessionExpireInSeconds)
    sessionExpireDatetime = currentDatetime + timeDelta

    if x_FacebookAccessToken is None:
        # Anonymous User
        anonymousUser = UserService.createAnonymousUser(dbSession=dbSession)
        anonymousUserSession = UserService.createUserSession(
            userProfile=anonymousUser,
            expire=sessionExpireDatetime,
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
        expire=sessionExpireDatetime,
        dbSession=dbSession
    )
    logger.info(f"created session for {x_FacebookAccessToken[:10]=}, {session.sessionToken[:10]=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username=user.username,
    )
