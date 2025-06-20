import jwt
import requests
import typing as t

from urllib.parse import urlencode

from pydantic import BaseModel
from pydantic import ValidationError

from ..config import settings
from ..logger import logger
from .Services.Base import ServiceWithLogging
from .exception import CognitoServiceError


class CognitoDecodedAccessToken(BaseModel):
    iss: str
    client_id: str
    token_use: str


class CognitoUserInfo(BaseModel):
    email: str
    username: str


class CognitoService(ServiceWithLogging):
    class CognitoMetadata:
        class Metadata(BaseModel):
            authorization_endpoint: str
            end_session_endpoint: str
            id_token_signing_alg_values_supported: list[str]
            issuer: str
            jwks_uri: str
            userinfo_endpoint: str

        metadata: t.Optional[Metadata]

        def __init__(self):
            if settings.cognitoConfig is None:
                self.metadata = None
                return
            logger.debug(f"Fetching Metadata @{settings.cognitoConfig.serverMetadataUrl}")
            data = requests.get(
                settings.cognitoConfig.serverMetadataUrl,
                headers={"Accept": "application/json"}
            ).json()
            self.metadata = self.Metadata.model_validate(data)

    def __init__(self, cognitoMetadata: CognitoMetadata) -> None:
        super().__init__(serviceName="CognitoService")
        self.metadata = cognitoMetadata.metadata
        if self.metadata is None:
            return

    def getLoginUrl(self, callbackUrl: str) -> str:
        """
        Constructs the login URL for the Cognito service.

        :param redirectUrl: The URL to redirect to after login.
        """
        self.setLoggerAdditionalPrefix(f"getLoginUrl")
        if self.metadata is None or settings.cognitoConfig is None:
            raise CognitoServiceError.NotAvalableError()
        self.loggerDebug(f"Constructing login URL with callbackUrl: {callbackUrl}")
        self.loggerDebug(f"Using Cognito authorization endpoint: {self.metadata.authorization_endpoint}")
        redirectUrl = f"{self.metadata.authorization_endpoint}?" + urlencode({
            "client_id": settings.cognitoConfig.clientId,
            "response_type": "token",
            "scope": "email openid",
            "redirect_uri": callbackUrl
        })
        self.loggerDebug(f"Constructed redirect URL: {redirectUrl}")
        return redirectUrl

    def parseAndValidateAccessToken(self, token: str) -> CognitoDecodedAccessToken:
        """Validates the access token against the Cognito service."""
        self.setLoggerAdditionalPrefix(f"validateAccessToken][{token[-10:]=}")
        if not token:
            raise CognitoServiceError.InvalidTokenError("Access token is empty or None.")
        if self.metadata is None or settings.cognitoConfig is None:
            raise CognitoServiceError.NotAvalableError()
        client = jwt.PyJWKClient(self.metadata.jwks_uri)
        publicKey = client.get_signing_key_from_jwt(token).key
        try:
            decoded = jwt.decode(  # type: ignore
                token,
                publicKey,
                algorithms=self.metadata.id_token_signing_alg_values_supported,
                verify=True,
            )
            self.loggerDebug(f"Decoded JWT token: {decoded}")
            accessToken = CognitoDecodedAccessToken.model_validate(decoded)
            if accessToken.client_id != settings.cognitoConfig.clientId:
                self.loggerWarning(f"JWT token client_id mismatch: {accessToken.client_id} != {settings.cognitoConfig.clientId}")
                raise CognitoServiceError.InvalidTokenError("Client ID mismatch in JWT token.")
            if accessToken.token_use != "access":
                self.loggerWarning(f"JWT token token_use mismatch: {accessToken.token_use} != 'access'")
                raise CognitoServiceError.InvalidTokenError("Invalid Token use")
            if accessToken.iss != self.metadata.issuer:
                self.loggerWarning(f"JWT token issuer mismatch: {accessToken.iss} != {self.metadata.issuer}")
                raise CognitoServiceError.InvalidTokenError("Issuer mismatch in JWT token.")
            return accessToken
        except jwt.ExpiredSignatureError:
            self.loggerWarning("JWT token has expired for user")
            raise CognitoServiceError.TokenExpiredError("JWT token has expired.")
        except jwt.InvalidTokenError as e:
            self.loggerWarning(f"Invalid JWT token: {str(e)}")
            raise CognitoServiceError.InvalidTokenError(f"Invalid JWT token")
        except ValidationError as e:
            self.loggerWarning(f"Invalid JWT token: {str(e)}")
            raise CognitoServiceError.InvalidTokenError("Invalid JWT token format.")

    def fetchUserInfo(self, token: str) -> dict[str, str]:
        if self.metadata is None:
            raise CognitoServiceError.NotAvalableError()
        return requests.get(self.metadata.userinfo_endpoint, headers={
            "Authorization": f"Bearer {token}"
        }).json()

    def getUserFromAccessToken(self, token: str) -> CognitoUserInfo:
        """
        Parses the JWT token and returns the URL information.

        :param token: The JWT token to parse.
        :return: class CognitoUserInfo
        """
        self.setLoggerAdditionalPrefix(f"getUserFromAccessToken][{token[-10:]=}")
        self.parseAndValidateAccessToken(token)
        self.loggerDebug("Fetching user info endpoint")
        info = CognitoUserInfo.model_validate(self.fetchUserInfo(token))
        self.loggerDebug(f"Returning UserInfo: {info}")
        return info
