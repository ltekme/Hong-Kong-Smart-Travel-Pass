import time
import typing as t

from fastapi import APIRouter
from fastapi import Request
from fastapi import Header
from fastapi.responses import RedirectResponse

from APIv2.logger import logger
from APIv2.dependence import dbSessionDepend
from APIv2.dependence import getCognitoServiceDepend
from APIv2.dependence import getUserServiceDepend
from APIv2.dependence import getUserSessionServiceDepend
from APIv2.modules.exception import AuthorizationError
from APIv2.config import settings
from ..models import AuthDataModel


router = APIRouter(prefix="/cognito")


@router.get("", response_model=AuthDataModel.Response)
async def cognitoLogin(
    dbSession: dbSessionDepend,
    getCognitoService: getCognitoServiceDepend,
    getUserService: getUserServiceDepend,
    getUserSessionService: getUserSessionServiceDepend,
    authorizationHeader: t.Annotated[str, Header(alias="Authorization")] = ""
) -> AuthDataModel.Response:
    if not authorizationHeader.startswith("Bearer"):
        raise AuthorizationError("Not Authorized")
    cognitoService = getCognitoService()
    userService = getUserService(dbSession)
    accessToken = authorizationHeader.split(" ")[1]
    userInfo = cognitoService.getUserFromAccessToken(accessToken)
    logger.debug(f"User info from Cognito: {userInfo}")
    user = userService.createOrGetAuthenticatedUser(userInfo.email, userInfo.username)
    userSession = getUserSessionService(dbSession).createForUser(user)
    dbSession.commit()
    logger.debug(f"Created user session: {userSession.sessionToken}")
    return AuthDataModel.Response(
        sessionToken=userSession.sessionToken,
        expireEpoch=int(time.mktime(userSession.expire.timetuple())),
        username=user.username
    )


@router.get("/redirect", response_class=RedirectResponse)
async def cognitoLoginRedirect(
    request: Request,
    getCognitoService: getCognitoServiceDepend,
) -> RedirectResponse:
    """Redirect to Cognito login page"""
    redirectUrl = getCognitoService().getLoginUrl(f"{settings.applicationPublicUrl}/auth/callback")
    logger.debug(f"Constructed redirectUrl {redirectUrl}")
    return RedirectResponse(url=redirectUrl)
