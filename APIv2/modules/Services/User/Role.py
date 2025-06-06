import typing as t

from ..base import ServiceBase
from ...ApplicationModel import Role
from ..Permission.Permission import PermissionService
from ..Permission.RolePermission import RolePermissionService
from ..Permission.PermissionDefinations import (
    CHATLLM_CREATE,
    CHATLLM_INVOKE,
)

import sqlalchemy.orm as so


class RoleService(ServiceBase):
    def __init__(self, dbSession: so.Session, permissionService: PermissionService, rolePermissionService: RolePermissionService) -> None:
        super().__init__(dbSession)
        self.permissionService = permissionService
        self.rolePermissionService = rolePermissionService

    def createRole(self, name: str, description: t.Optional[str] = None) -> Role:
        """
        Create a user role.
        :param name: The name of the role.
        :param description: A description of the role.
        :return: The user role instance.
        """
        instance = Role(name=name, description=description)
        self.dbSession.add(instance)
        return instance

    def getByName(self, name: str):
        """
        Get a user role by its name.
        :param name: The name of the role to search for.
        :return: The user role instance or None if not found.
        """
        return self.dbSession.query(Role).where(Role.name == name).first()

    def getOrCreateRole(self, name: str, description: t.Optional[str] = None) -> Role:
        """
        Get a user role by its name or create it if it does not exist.
        :param name: The name of the role to search for.
        :param description: A description of the role.
        :return: The user role instance.
        """
        role = self.getByName(name)
        if not role:
            role = self.createRole(name, description)
        return role

    def getOrCreateAnonymousRole(self) -> Role:
        """
        Get or create the anonymous role.
        :return: The anonymous user role instance.
        """
        defaultRolePermission = [
            self.permissionService.getOrCreatePermission(CHATLLM_INVOKE),
            self.permissionService.getOrCreatePermission(CHATLLM_CREATE),
        ]
        role = self.getOrCreateRole(name="Anonymous", description="Role for anonymous users")
        if not role.permissions:
            # Assign default permissions to the anonymous role if not already assigned
            self.dbSession.add(role)
            for permission in defaultRolePermission:
                self.rolePermissionService.createRolePermissionAssociation(
                    role=role,
                    permission=permission,
                    effect=True
                )
        return role
