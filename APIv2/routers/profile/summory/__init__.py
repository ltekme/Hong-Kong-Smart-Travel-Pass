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
from ....dependence import (
    dbSessionDepend,
    getUserSessionServiceDepend,
    getUserServiceDepend
)
from ....config import logger
from ....modules.Services.social import FacebookService, SocialProfileService, SocialProviderService

router = APIRouter(prefix="/summory")


@router.get("", response_model=ProfileSummoryGet.Response)
async def requestSummoryGet(
    dbSession: dbSessionDepend,
    getUserSessionService: getUserSessionServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ProfileSummoryGet.Response:
    """Get Current User Profile Summory"""
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    summorys: list[str] = []
    for i in session.user.socials:
        if i.socialProfileSummory is not None:
            summorys.append(i.socialProfileSummory)
    return ProfileSummoryGet.Response(
        summory="".join(summorys),
        lastUpdate=session.user.socials[-1].lastUpdate,
    )


@router.post("", response_model=ProfileSummoryRequest.Response)
async def requestSummory(
    dbSession: dbSessionDepend,
    getUserService: getUserServiceDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> ProfileSummoryRequest.Response:
    """Request user profile summory"""
    if x_FacebookAccessToken is None:
        raise HTTPException(
            status_code=400,
            detail="Facebook Access Token not provided"
        )
    facebookClient = FacebookClient.FacebookClient()
    socialProfileService = SocialProfileService(dbSession)
    facebookService = FacebookService(
        dbSession=dbSession,
        userService=getUserService(dbSession),
        socialProfileService=socialProfileService,
        socialProviderService=SocialProviderService(dbSession),
        facebookClient=facebookClient,
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
