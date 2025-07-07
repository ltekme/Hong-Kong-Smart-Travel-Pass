import typing as t

import sqlalchemy.orm as so

from ..Base import ServiceBase
from ..PermissionAndQuota.Permission import PermissionService
from ..PermissionAndQuota.Quota import QuotaService
from APIv2.modules.ApplicationModel import Role


class RoleService(ServiceBase):
    def __init__(self,
                 dbSession: so.Session,
                 permissionService: PermissionService,
                 qoutaService: QuotaService,
                 ) -> None:
        super().__init__(dbSession, serviceName="RoleService")
        self.permissionService = permissionService
        self.qoutaService = qoutaService

    def createRole(self, name: str, description: t.Optional[str] = None) -> Role:
        """
        Create a user role.
        :param name: The name of the role.
        :param description: A description of the role.
        :return: The user role instance.
        """
        self.loggerDebug(f"Creating role with name: {name}, description: {description}")
        instance = Role(name=name, description=description)
        self.dbSession.add(instance)
        return instance

    def getByName(self, name: str):
        """
        Get a user role by its name.
        :param name: The name of the role to search for.
        :return: The user role instance or None if not found.
        """
        self.loggerDebug(f"Getting role by name: {name}")
        return self.dbSession.query(Role).where(Role.name == name).first()

    def getOrCreateRole(self, name: str, description: t.Optional[str] = None) -> Role:
        """
        Get a user role by its name or create it if it does not exist.
        :param name: The name of the role to search for.
        :param description: A description of the role.
        :return: The user role instance.
        """
        self.loggerDebug(f"Getting or creating role with name: {name}, description: {description}")
        role = self.getByName(name)
        if not role:
            self.loggerDebug(f"Role with name: {name} not found, creating new one.")
            role = self.createRole(name, description)
        return role
