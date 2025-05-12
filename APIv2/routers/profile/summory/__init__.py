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
    UserService
)
from ....dependence import dbSessionDepend
from ....config import logger


router = APIRouter(prefix="/summory")


@router.get("", response_model=ProfileSummoryGet.Response)
async def requestSummoryGet(
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ProfileSummoryGet.Response:
    """Get Current User Profile Summory"""
    if x_SessionToken is None:
        raise HTTPException(
            status_code=400,
            detail="No sessionToken found"
        )
    logger.debug(f"performing user lookup for {x_SessionToken[:10]=}")
    userProfile = UserService.getUserProfileFromSessionToken(
        sessionToken=x_SessionToken,
        dbSession=dbSession,
        bypassExpire=False
    )
    if userProfile is None:
        logger.debug(f"Userprofile with {x_SessionToken[:10]=} was not found")
        raise HTTPException(
            status_code=404,
            detail="No User Found"
        )

    summorys: list[str] = []
    for i in userProfile.socials:
        if i.profileSummory is not None:
            summorys.append(i.profileSummory)

    return ProfileSummoryGet.Response(
        summory="".join(summorys),
        lastUpdate=userProfile.socials[-1].lastUpdate,
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

    try:
        logger.debug(f"performing user details lookup for {x_FacebookAccessToken[:10]=}")
        userProfileDetails = FacebookClient.getUserProfileDetails(accessToken=x_FacebookAccessToken)
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

    logger.debug(f"Updating personalization summory for {x_FacebookAccessToken[:10]=}")
    facebookProfile = FacebookClient.getUsernameAndId(accessToken=x_FacebookAccessToken)
    provider = UserService.getOrCreateSocialsProfileProvider('facebook', dbSession)
    userSocialProfile = UserService.queryUserSocialProfile(
        socialId=str(facebookProfile.facebookId),
        provider=provider,
        dbSession=dbSession
    )
    if userSocialProfile is None:
        return ProfileSummoryRequest.Response(
            success=False,
            summory="Not Found",
        )
    userSocialProfile.profileSummory = userProfileSummory
    userSocialProfile.lastUpdate = datetime.datetime.now(datetime.UTC)
    dbSession.commit()

    return ProfileSummoryRequest.Response(
        success=True,
        summory=userProfileSummory,
    )
