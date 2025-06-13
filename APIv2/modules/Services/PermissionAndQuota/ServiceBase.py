import typing as t
import sqlalchemy.orm as so

from .Permission import PermissionService, NoPermssionError
from .Quota import QuotaService, QoutaExceededError

from ...ApplicationModel import User
from ...Services.Base import ServiceBase
from ..ServiceDefination import ServiceActionDefination


class ServiceWithAAA(ServiceBase):
    def __init__(self,
                 dbSession: so.Session,
                 serviceName: str,
                 quotaService: QuotaService,
                 permissionService: PermissionService,
                 user: t.Optional[User] = None) -> None:
        super().__init__(dbSession, serviceName)
        self.user = user
        self.permissionService = permissionService
        self.quotaService = quotaService

    def checkPermission(self, actionId: int) -> bool:
        """
        Check if a user has permission to invoke the chat service specified by the action.

        :param user: The user profile to check permissions for.
        :param action: The action to check permissions against.
        :return: True if the user has permission, False otherwise.
        """
        if not self.user:
            self.loggerWarning("No user provided, Assuming Public With Permission.")
            return True

        permission = self.permissionService.getOrCreatePermission(actionId)
        self.loggerDebug(f"Checking if {self.user.id=} has permission to invoke chat service")
        return self.permissionService.hasPermission(self.user, permission)

    def checkQouta(self, actionId: int) -> bool:
        """
        Check if the user has quota for the specified action.

        :param actionId: The ID of the action to check quota for.
        :return: True if the user has quota, False otherwise.
        """
        if not self.user:
            self.loggerWarning("No user provided, Assuming Public With Permission.")
            return True

        self.loggerDebug(f"Checking if {self.user.id=} has quota for action {actionId}")
        remaining = self.quotaService.userHasQuotaRemaining(self.user, actionId)

        return remaining

    def checkAndIncrementQuota(self, actionId: int) -> bool:
        """
        Check if the user has quota for the specified action and increment the quota usage.

        :param actionId: The ID of the action to check quota for.
        :return: True if the user has quota, False otherwise.
        """
        if not self.checkQouta(actionId):
            return False

        if not self.user:
            self.loggerWarning("No user provided, Assuming Public With Permission.")
            return True

        self.loggerDebug(f"Incrementing quota usage for user {self.user.id} for actionId {actionId}")
        self.quotaService.incrementQuotaUsage(
            user=self.user,
            actionId=actionId,
            increment=1,
        )
        return True


def permissionRequired(
    action: str,
):
    """
    A decorator to validate user permissions for a specific action.
    Throws a PermissionError if the user does not have permission to perform the action.
    If bypassPermissionCheck is set to True in the kwargs, permission check will be skipped.
    :param action: The the action to check permissions for or the string name of the action.

    example usage:
    @validatePermission(INVOKE)
    def invokeChatModel(self, chatId: str, message: ChatMessage, contextValues: InvokeContextValues,
                        bypassPermssionCheck: bool = False,
                        bypassChatAssociationCheck: bool = False,
                        bypassQuotaCheck: bool = False,
                        ) -> ChatMessage:

    This decorator can only be used on the methods of a class that inherits from ServiceWithAAA.

    """
    def decorator(func: t.Callable[..., t.Any]):
        def wrapper(*args: t.Any, **kwargs: dict[str, t.Any]) -> t.Any:
            self = args[0]
            if not issubclass(self.__class__, ServiceWithAAA):
                raise TypeError("This decorator can only be used on methods of a class that inherits from ServiceWithAAA.")
            actionId = ServiceActionDefination.getId(action)
            if not kwargs.get('bypassPermissionCheck', False):
                hasPermission = self.checkPermission(actionId)
                if not hasPermission:
                    raise NoPermssionError(action)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def quotaRequired(
    action: str,
):
    """
    A decorator to validate user quota for a specific action.
    Throws a QoutaExceededError if the user does not have quota to perform the action.
    If bypassQuotaCheck is set to True in the kwargs, quota check will be skipped.
    :param action: The the action to check permissions for or the string name of the action.

    example usage:
    @validatePermission(INVOKE)
    def invokeChatModel(self, chatId: str, message: ChatMessage, contextValues: InvokeContextValues,
                        bypassPermssionCheck: bool = False,
                        bypassChatAssociationCheck: bool = False,
                        bypassQuotaCheck: bool = False,
                        ) -> ChatMessage:

    This decorator can only be used on the methods of a class that inherits from ServiceWithAAA.

    """
    def decorator(func: t.Callable[..., t.Any]):
        def wrapper(*args: t.Any, **kwargs: dict[str, t.Any]) -> t.Any:
            self = args[0]
            if not issubclass(self.__class__, ServiceWithAAA):
                raise TypeError("This decorator can only be used on methods of a class that inherits from ServiceWithAAA.")
            actionId = ServiceActionDefination.getId(action)
            if not kwargs.get('bypassQuotaCheck', False):
                hasQouta = self.checkAndIncrementQuota(actionId)
                if not hasQouta:
                    raise QoutaExceededError(f"User {self.user.id} does not have permission to perform {action}.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
