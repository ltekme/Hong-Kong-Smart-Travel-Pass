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
from ....modules.FacebookClient import FacebookClient
from ....modules.Services.user import UserSessionService, UserTypeService, UserService
from ....modules.Services.social import FacebookService, SocialProfileService, SocialProviderService, FacebookUserIdentifyExeception

router = APIRouter(prefix="/auth")


@router.get("", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken for a user"""
    userService = UserService(dbSession, UserTypeService(dbSession))
    userSessionService = UserSessionService(dbSession)
    facebookService = FacebookService(
        dbSession=dbSession,
        userService=userService,
        socialProfileService=SocialProfileService(dbSession),
        socialProviderService=SocialProviderService(dbSession),
        facebookClient=FacebookClient(),
    )
    if x_FacebookAccessToken is None:
        # Anonymous User
        anonymousUser = userService.createAnonymous()
        anonymousUserSession = userSessionService.createForUserProfile(anonymousUser)
        logger.info(f"Created session for anonymous user {anonymousUser.username=}")
        dbSession.commit()
        return AuthDataModel.Response(
            sessionToken=anonymousUserSession.sessionToken,
            expireEpoch=int(time.mktime(anonymousUserSession.expire.timetuple())),
            username=anonymousUser.username,
        )
    try:
        user = facebookService.getOrCreateUserProfileFromAccessToken(x_FacebookAccessToken)
    except FacebookUserIdentifyExeception as e:
        logger.warning(e)
        raise HTTPException(
            status_code=400,
            detail=e
        )
    logger.info(f"Removing existing session for {user.id=}")
    userSessionService.clearExpiredUserSession(user)
    logger.info(f"Creating session for {x_FacebookAccessToken[:10]=}")
    session = userSessionService.createForUserProfile(user)
    logger.info(f"created session for {x_FacebookAccessToken[:10]=}, {session.sessionToken[:10]=}")
    dbSession.commit()
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
    userSessionService = UserSessionService(dbSession)
    session = userSessionService.updateExpiration(x_SessionToken)
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
