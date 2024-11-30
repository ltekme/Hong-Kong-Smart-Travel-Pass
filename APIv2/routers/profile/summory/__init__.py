import logging
from fastapi import (
    APIRouter,
    HTTPException,
)
import datetime

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


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/summory")


@router.get("/", response_model=ProfileSummoryGet.Response)
async def requestSummoryGet(
    request: ProfileSummoryGet.Request,
    dbSession: dbSessionDepend,
) -> ProfileSummoryGet.Response:
    """Get Current User Profile Summory"""
    sessionToken = request.sessionToken
    currentDatetime = datetime.datetime.now()

    try:
        logger.debug(f"performing user lookup for {sessionToken[:10]=}")
        userSesion = ApplicationModel.UserProfileSession.get(
            sessionToken=sessionToken,
            currentTime=currentDatetime,
            dbSession=dbSession,
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Error getting user"
        )

    if userSesion is None:
        logger.debug(f"{sessionToken[:10]=} was not found")
        raise HTTPException(
            status_code=404,
            detail="No User Found"
        )

    return ProfileSummoryGet.Response(
        summory=userSesion.personalizationSummory
    )


@router.post("/request", response_model=ProfileSummoryRequest.Response)
async def requestSummory(
    request: ProfileSummoryRequest.Request,
    dbSession: dbSessionDepend,
) -> ProfileSummoryRequest.Response:
    """Request user profile summory"""
    accessToken = request.accessToken

    try:
        logger.debug(f"performing user details lookup for {accessToken[:10]=}")
        userProfileDetails = FacebookClient.getUserProfileDetails(accessToken=accessToken)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Error getting user details"
        )

    try:
        logger.debug(f"generating user lookup for {accessToken[:10]=}")
        userProfileSummory = UserProfiling.generateUserProfileSummory(userProfileDetails)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Error generating profile summory"
        )

    try:
        userProfile = ApplicationModel.UserProfile.fromFacebookAccessToken(
            accessToken=accessToken,
            dbSession=dbSession
        )
        userProfile.personalizationSummory = userProfileSummory
        userProfile.personalizationSummoryLastUpdate = datetime.datetime.now()
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
