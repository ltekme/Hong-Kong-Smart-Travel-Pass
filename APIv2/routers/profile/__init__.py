import time
import datetime
from fastapi import (
    APIRouter,
    HTTPException,
    Response,
)
from . import summory
from ..profile.models import AuthDataModel
from ...modules.ApplicationModel import (
    UserProfile,
    UserProfileSession,
    FacebookUserIdentifyExeception,
)
from ...dependence import (
    dbSessionDepend,
)
from ...config import (
    logger,
    settings,
    ClientCookiesKeys,
)


router = APIRouter(prefix="/profile")
router.include_router(summory.router)


@router.post("/auth", response_model=AuthDataModel.Response)
async def auth(
    request: AuthDataModel.Request,
    response: Response,
    dbSession: dbSessionDepend,
) -> AuthDataModel.Response:
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
    response.set_cookie(
        key=ClientCookiesKeys.SESSION_TOKEN,
        value=session.sessionToken
    )
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple()))
    )
