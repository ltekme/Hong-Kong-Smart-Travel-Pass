import typing as t
import sqlalchemy.orm as so

from .Services.Base import ServiceBase
from .Services.ServiceDefination import ServiceActionDefination

from .ApplicationModel import ServiceConfig as ServiceConfigModel


class ServiceDisabledError(Exception):
    """Exception raised when a service is disabled."""

    def __init__(self, action: str) -> None:
        super().__init__(f"Service for action '{action}' is disabled.")
        self.action = action


class ServiceConfig(ServiceBase):
    def __init__(self, dbSession: so.Session) -> None:
        super().__init__(dbSession, "ConfigService")

    def create(self, actionId: int, enabled: bool = True) -> ServiceConfigModel:
        """
        Create a new service configuration by action.

        :param action: The action for which the service configuration is created.
        :param enabled: Whether the service is enabled or not.
        :return: The created ServiceConfigModel instance.
        """
        self.loggerDebug(f"Creating service configuration for actionId: {actionId}, enabled: {enabled}")
        serviceConfig = ServiceConfigModel(actionId=actionId, enabled=enabled)
        self.dbSession.add(serviceConfig)
        self.loggerInfo(f"Service configuration created for action: {actionId}")
        return serviceConfig

    def get(self, actionId: int) -> t.Optional[ServiceConfigModel]:
        """
        Get the service configuration by its ID.

        :param serviceId: The ID of the service configuration.
        :return: The ServiceConfigModel instance.
        """
        self.loggerDebug(f"Fetching service configuration for actionId: {actionId}")
        return self.dbSession.query(ServiceConfigModel).where(ServiceConfigModel.actionId == actionId).first()

    def getOrCreateByAction(self, action: str, enabled: bool = True) -> ServiceConfigModel:
        """
        Get or create a service configuration by action.

        :param action: The action for which the service configuration is fetched or created.
        :param enabled: Whether the service is enabled or not.
        :return: The ServiceConfigModel instance.
        """
        self.loggerDebug(f"Getting or creating service configuration for action: {action}")
        actionId = ServiceActionDefination.getId(action)
        serviceConfig = self.get(actionId)
        if serviceConfig:
            self.loggerInfo(f"Service configuration found for action: {action}, returning config.")
            return serviceConfig

        self.loggerInfo(f"Service configuration not found for action: {action}, creating new config.")
        return self.create(actionId, enabled)

    def actionEndabled(self, action: str) -> bool:
        """
        Check if the service is enabled for the given action.

        :param action: The action to check.
        :return: True if the service is enabled, False otherwise.
        """
        self.loggerInfo(f"Checking if service is enabled for action: {action}")
        enabled = self.getOrCreateByAction(action).enabled
        self.loggerInfo(f"Service enabled status for action '{action}': {enabled}")
        return self.getOrCreateByAction(action).enabled


def checksEnabled(action: str):
    """
    A decorator to validate user permissions for a specific action.
    Throws a ServiceDisabledError if the service for the action is disabled.
    If bypassServiceConfig is set to True in the kwargs, permission check will be skipped.
    :param action: The the action to check permissions for or the string name of the action.

    example usage:
    @checksEnabled(INVOKE)
    def invokeChatModel(self, chatId: str, message: ChatMessage, contextValues: InvokeContextValues,
                        bypassServiceEnable: bool = False,
                        ) -> ChatMessage:

    This decorator can only be used on the methods of a class that inherits from ServiceBase.
    """
    def decorator(func: t.Callable[..., t.Any]):
        def wrapper(*args: t.Any, **kwargs: dict[str, t.Any]) -> t.Any:
            self: ServiceBase = args[0]
            if not isinstance(self, ServiceBase):  # type: ignore
                raise TypeError("This decorator can only be used on methods of a class that inherits from ServiceBase.")
            if not kwargs.get('bypassServiceEnable', False):
                serivceConfig = ServiceConfig(self.dbSession)
                if not serivceConfig.actionEndabled(action):
                    raise ServiceDisabledError(action)
            return func(*args, **kwargs)
        return wrapper
    return decorator
