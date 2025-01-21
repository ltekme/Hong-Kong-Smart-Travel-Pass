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
)


router = APIRouter(prefix="/profile")
router.include_router(summory.router)


@router.get("/auth", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    x_FacebookAccessToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """ Get sessionToken for a user from facebook access token"""
    # TODO: impliment public&private key pairing to hash the facebook access token before sending

    if x_FacebookAccessToken is None:
        raise HTTPException(
            status_code=400,
            detail="Facebook Access Token not provided"
        )

    try:
        logger.debug(f"Preping session for {x_FacebookAccessToken[:10]=}")
        currentDatetime = datetime.datetime.now(datetime.UTC)
        timeDelta = datetime.timedelta(seconds=settings.sessionExpireInSeconds)
        sessionExpireDatetime = currentDatetime + timeDelta

        logger.debug(f"Performing user lookup for {x_FacebookAccessToken[:10]=}")
        userProfile = UserProfile.fromFacebookAccessToken(
            accessToken=x_FacebookAccessToken,
            dbSession=dbSession
        )

        logger.debug(f"Removing existing session for {userProfile.facebookId=}")
        UserProfileSession.clearProfile(
            userProfile=userProfile,
            dbSession=dbSession,
        )

        logger.debug(f"Creating session for {x_FacebookAccessToken[:10]=}")
        session = UserProfileSession.create(
            userProfile=userProfile,
            expire=sessionExpireDatetime,
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

    logger.debug(f"created session for {x_FacebookAccessToken[:10]=}, {session.sessionToken[:10]=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple()))
    )
