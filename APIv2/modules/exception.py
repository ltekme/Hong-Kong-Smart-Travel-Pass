class AuthorizationError(Exception):
    """Raised when an attempt to authorize an entitiy failed"""


class NotAuthorizedError(Exception):
    """Raised when an attempt to access resource failed due to insufficient permission"""

    def __init__(self, message: str, action: str) -> None:
        super().__init__(message)
        self.action = action


class ConfigurationError(Exception):
    """Raised when a configuration error accored."""


class InsufficientQoutaError(Exception):
    "Raised when qouta is insufficient to perform an action"


class ChatLLMServiceError(Exception):
    """Base exception class for ChatLLMService errors."""


class CognitoServiceError(Exception):
    class TokenExpiredError(Exception):
        """Exception raised when the JWT token has expired."""

    class InvalidTokenError(Exception):
        """Exception raised when the JWT token is invalid."""

    class NotAvalableError(Exception):
        """Exception raised when Auth is not avalable"""

class ServiceDisabledError(Exception):
    """Exception raised when a service is disabled."""

    def __init__(self, action: str) -> None:
        super().__init__(f"Service for action '{action}' is disabled.")
        self.action = action
