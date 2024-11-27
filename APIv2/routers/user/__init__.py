import time
import logging
import datetime
from fastapi import APIRouter, HTTPException

from .models import (
    AuthDataModel,
    RequestProfileSummory,
)
from ...modules.ApplicationModel import (
    UserProfile,
    UserProfileSession,
    FacebookUserIdentifyExeception,
)
from ...modules import (
    UserProfiling,
    FacebookClient,
)
from ...dependence import dbSessionDepend
from ...config import settings


router = APIRouter(prefix="/user")
logger = logging.getLogger(__name__)


@router.post("/auth", response_model=AuthDataModel.Response)
def auth(request: AuthDataModel.Request, dbSession: dbSessionDepend) -> AuthDataModel.Response:
    """ Get sessionToken for a user from facebook access token"""
    # TODO: impliment public&private key pairing to hash the facebook access token before sending
    accessToken = request.accessToken
    currentDatetime = datetime.datetime.now()
    timeDelta = datetime.timedelta(seconds=settings.sessionExpireInSeconds)
    sessionExpireDatetime = currentDatetime + timeDelta

    try:
        logger.debug(f"performing user lookup for {accessToken[:10]=}")
        userProfile = UserProfile.fromFacebookAccessToken(
            accessToken=accessToken,
            dbSession=dbSession
        )
    except FacebookUserIdentifyExeception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail=e
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Server Error"
        )

    try:
        logger.debug(f"creating session for {accessToken[:10]=}")
        session = UserProfileSession.create(
            profile=userProfile,
            expire=sessionExpireDatetime,
            dbSession=dbSession
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail="Server Error"
        )

    logger.debug(f"created session for {accessToken[:10]=}, {session.sessionToken[:10]=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple()))
    )


@router.post("/requestProfileSummory", response_model=RequestProfileSummory.Response)
def requestProfileSummory(
    request: RequestProfileSummory.Request,
    dbSession: dbSessionDepend,
) -> RequestProfileSummory.Response:
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
        userProfile = UserProfile.fromFacebookAccessToken(
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

    return RequestProfileSummory.Response(
        success=True,
        summory=userProfileSummory,
    )
