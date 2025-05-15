import datetime
import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header,
)

from .models import (
    ProfileSummoryRequest,
    ProfileSummoryGet,
)
from ....modules import (
    FacebookClient,
    LlmHelper,
)
from ....dependence import dbSessionDepend
from ....config import logger

from ....modules.Services.user import UserService, UserSessionService, UserTypeService
from ....modules.Services.social import FacebookService, SocialProfileService, SocialProviderService

router = APIRouter(prefix="/summory")


@router.get("", response_model=ProfileSummoryGet.Response)
async def requestSummoryGet(
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ProfileSummoryGet.Response:
    userSessionService = UserSessionService(dbSession)
    """Get Current User Profile Summory"""
    if x_SessionToken is None:
        raise HTTPException(
            status_code=400,
            detail="No sessionToken found"
        )
    logger.debug(f"performing user lookup for {x_SessionToken[:10]=}")
    userSession = userSessionService.getSessionFromSessionToken(
        sessionToken=x_SessionToken,
        bypassExpire=False
    )
    if userSession is None:
        logger.debug(f"userSession with {x_SessionToken[:10]=} was not found")
        raise HTTPException(
            status_code=404,
            detail="No User Found"
        )

    summorys: list[str] = []
    for i in userSession.profile.socials:
        if i.socialProfileSummory is not None:
            summorys.append(i.socialProfileSummory)

    return ProfileSummoryGet.Response(
        summory="".join(summorys),
        lastUpdate=userSession.profile.socials[-1].lastUpdate,
    )


@router.post("", response_model=ProfileSummoryRequest.Response)
async def requestSummory(
    dbSession: dbSessionDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> ProfileSummoryRequest.Response:
    """Request user profile summory"""

    if x_FacebookAccessToken is None:
        raise HTTPException(
            status_code=400,
            detail="Facebook Access Token not provided"
        )
    facebookClient = FacebookClient.FacebookClient()
    userTypeService = UserTypeService(dbSession)
    userService = UserService(dbSession, userTypeService)
    socialProviderService = SocialProviderService(dbSession)
    socialProfileService = SocialProfileService(dbSession)
    facebookService = FacebookService(
        dbSession=dbSession,
        userService=userService,
        socialProfileService=socialProfileService,
        socialProviderService=socialProviderService,
        facebookClient=facebookClient
    )
    logger.debug(f"Updating personalization summory for {x_FacebookAccessToken[:10]=}")
    facebookProfile = facebookClient.getUsernameAndId(accessToken=x_FacebookAccessToken)
    userSocialProfile = socialProfileService.get(
        socialId=str(facebookProfile.facebookId),
        provider=facebookService.provider,
    )
    if userSocialProfile is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    try:
        logger.debug(f"performing user details lookup for {x_FacebookAccessToken[:10]=}")
        userProfileDetails = facebookClient.getUserProfileDetails(accessToken=x_FacebookAccessToken)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Error getting user details"
        )
    try:
        logger.debug(f"generating user lookup for {x_FacebookAccessToken[:10]=}")
        userProfileSummory = LlmHelper.generateUserProfileSummory(userProfileDetails)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Error generating profile summory"
        )
    userSocialProfile.socialProfileSummory = userProfileSummory
    userSocialProfile.lastUpdate = datetime.datetime.now(datetime.UTC)
    dbSession.commit()
    return ProfileSummoryRequest.Response(
        success=True,
        summory=userProfileSummory,
    )
