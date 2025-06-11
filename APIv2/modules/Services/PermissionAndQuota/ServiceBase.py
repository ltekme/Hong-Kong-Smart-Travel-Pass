import typing as t
import sqlalchemy.orm as so

from ....config import logger
from .Permission import PermissionService
from .Quota import QuotaService

from ...ApplicationModel import User


class ServiceBase:
    def __init__(self, dbSession: so.Session) -> None:
        self.dbSession = dbSession


class ServiceWithAAA(ServiceBase):
    def __init__(self,
                 dbSession: so.Session,
                 quotaService: QuotaService,
                 permissionService: PermissionService,
                 user: t.Optional[User] = None) -> None:
        super().__init__(dbSession)
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
            logger.warning("No user provided, Assuming Public With Permission.")
            return True

        permission = self.permissionService.getOrCreatePermission(actionId)
        logger.info(f"Checking if {self.user.id=} has permission to invoke chat service")
        return self.permissionService.hasPermission(self.user, permission)

    def checkQouta(self, actionId: int) -> bool:
        """
        Check if the user has quota for the specified action.

        :param actionId: The ID of the action to check quota for.
        :return: True if the user has quota, False otherwise.
        """
        if not self.user:
            logger.warning("No user provided, Assuming Public With Quota.")
            return True

        quota = self.quotaService.getOrCreateQuotaByName(self.user, )

        return self.quotaService.atLimit(self.user, quota)
