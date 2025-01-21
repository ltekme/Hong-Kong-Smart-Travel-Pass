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
    UserProfiling,
    ApplicationModel,
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
    currentDatetime = datetime.datetime.now(datetime.UTC)

    if x_SessionToken is None:
        raise HTTPException(
            status_code=400,
            detail="No sessionToken found"
        )

    try:
        logger.debug(f"performing user lookup for {x_SessionToken[:10]=}")
        userProfile = ApplicationModel.UserProfileSession.get(
            sessionToken=x_SessionToken,
            currentTime=currentDatetime,
            dbSession=dbSession,
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Error getting user"
        )

    if userProfile is None:
        logger.debug(f"Userprofile with {x_SessionToken[:10]=} was not found")
        raise HTTPException(
            status_code=404,
            detail="No User Found"
        )

    return ProfileSummoryGet.Response(
        summory=userProfile.personalizationSummory,
        lastUpdate=userProfile.personalizationSummoryLastUpdate
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
        userProfileSummory = UserProfiling.generateUserProfileSummory(userProfileDetails)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Error generating profile summory"
        )

    try:
        logger.debug(f"Updating personalization summory for {x_FacebookAccessToken[:10]=}")
        userProfile = ApplicationModel.UserProfile.fromFacebookAccessToken(
            accessToken=x_FacebookAccessToken,
            dbSession=dbSession
        )
        userProfile.personalizationSummory = userProfileSummory
        userProfile.personalizationSummoryLastUpdate = datetime.datetime.now(datetime.UTC)
        dbSession.commit()
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Error saving profile summory"
        )

    return ProfileSummoryRequest.Response(
        success=True,
        summory=userProfileSummory,
    )
