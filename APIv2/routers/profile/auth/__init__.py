import time
import typing as t
from fastapi import APIRouter, Header

from . import cognito

from .models import AuthDataModel
from APIv2.dependence import dbSessionDepend
from APIv2.dependence import getUserServiceDepend
from APIv2.dependence import getUserSessionServiceDepend
from APIv2.dependence import getConfigServiceDepend
from APIv2.dependence import getTotpServiceDepend
from APIv2.logger import logger
from APIv2.modules.exception import AuthorizationError
from APIv2.modules.Services.ServiceDefination import REQUIRE_TOTP_FOR_ANNY

router = APIRouter(prefix="/auth")
router.include_router(cognito.router)


@router.get("", response_model=AuthDataModel.Response)
async def auth(
    dbSession: dbSessionDepend,
    getUserService: getUserServiceDepend,
    getTotpService: getTotpServiceDepend,
    getConfigService: getConfigServiceDepend,
    getUserSessionService: getUserSessionServiceDepend,
    authorizationHeader: t.Annotated[str, Header(alias="Authorization")] = ""
) -> AuthDataModel.Response:
    """Get sessionToken for anonymous user"""
    configService = getConfigService(dbSession)
    totpService = getTotpService()

    # verification if Application have require totp enabled
    if configService.actionEndabled(REQUIRE_TOTP_FOR_ANNY):
        if not authorizationHeader.startswith("TOTP"):
            raise AuthorizationError("Invalid Access Code")
        accessCode = authorizationHeader.split(" ")[1]
        if not totpService.verify(accessCode):
            raise AuthorizationError("Invalid Access Code")

    anonymousUser = getUserService(dbSession).createAnonymous()
    anonymousUserSession = getUserSessionService(dbSession).createForUser(anonymousUser)
    dbSession.commit()
    logger.info(f"Created session for anonymous user {anonymousUser.id=}")
    return AuthDataModel.Response(
        sessionToken=anonymousUserSession.sessionToken,
        expireEpoch=int(time.mktime(anonymousUserSession.expire.timetuple())),
        username=anonymousUser.username,
    )


@router.get("/ping", response_model=AuthDataModel.Response)
async def ping(
    dbSession: dbSessionDepend,
    getUserSessionService:  getUserSessionServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> AuthDataModel.Response:
    """Get sessionToken info for a user"""
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    dbSession.commit()
    logger.info(f"Updated session {session.sessionToken[:10]=} for {session.user.username=}")
    return AuthDataModel.Response(
        sessionToken=session.sessionToken,
        expireEpoch=int(time.mktime(session.expire.timetuple())),
        username=session.user.username,
    )
