from fastapi import (
    APIRouter,
    HTTPException,
    Request
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
from ....config import (
    logger,
    ClientCookiesKeys,
)

router = APIRouter(prefix="/summory")


@router.get("", response_model=ProfileSummoryGet.Response)
async def requestSummoryGet(
    request: Request,
    dbSession: dbSessionDepend,
) -> ProfileSummoryGet.Response:
    """Get Current User Profile Summory"""
    sessionToken = request.cookies.get(ClientCookiesKeys.SESSION_TOKEN)
    currentDatetime = datetime.datetime.now()

    if sessionToken is None:
        raise HTTPException(
            status_code=400,
            detail="No sessionToken found"
        )

    try:
        logger.debug(f"performing user lookup for {sessionToken[:10]=}")
        userProfile = ApplicationModel.UserProfileSession.get(
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

    if userProfile is None:
        logger.debug(f"{sessionToken[:10]=} was not found")
        raise HTTPException(
            status_code=404,
            detail="No User Found"
        )

    return ProfileSummoryGet.Response(
        summory=userProfile.personalizationSummory,
        lastUpdate=userProfile.personalizationSummoryLastUpdate
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
