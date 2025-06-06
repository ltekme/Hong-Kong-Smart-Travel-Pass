import typing as t

import sqlalchemy.orm as so

from ..base import ServiceBase
from ...ApplicationModel import (
    User,
    Permission,
    UserPermission,
    RolePermission,
)

from ....config import logger


class ServiceWithPermissions(ServiceBase):
    def __init__(self, dbSession: so.Session, serivceName: str, user: t.Optional[User] = None) -> None:
        super().__init__(dbSession)
        self.permissionService = PermissionService(dbSession)
        self.serviceName = serivceName
        self.user = user

    def cheackPermission(self, action: str) -> bool:
        """
        Check if a user has permission to invoke the chat service specified by the action.

        :param user: The user profile to check permissions for.
        :param action: The action to check permissions against.
        :return: True if the user has permission, False otherwise.
        """
        if not self.user:
            logger.warning("No user provided, Assuming Public With Permission.")
            return True

        permissionName = self.permissionService.getPermissionName(self.serviceName, action)

        logger.info(f"Getting permission instance for: {permissionName}")
        permission = self.permissionService.getOrCreatePermission(permissionName)

        logger.info(f"Checking if {self.user.id=} has permission to invoke chat service")
        return self.permissionService.hasPermission(self.user, permission)


class PermissionService(ServiceBase):

    @classmethod
    def getPermissionName(cls, serviceName: str, action: str) -> str:
        """
        Get the permission name for a specific service and action.

        :param serviceName: The name of the service.
        :param action: The action to get the permission name for.
        :return: The permission name.
        """
        return f"{serviceName}:{action}"

    def createPermission(self, name: str, description: t.Optional[str] = None) -> Permission:
        """
        Create a new permission.

        :param name: The name of the permission.
        :param description: A description of the permission.
        :return: The created permission instance.
        """
        instance = Permission(name=name, description=description)
        self.dbSession.add(instance)
        return instance

    def getPermissionByName(self, name: str) -> t.Optional[Permission]:
        """
        Get a permission by its name.

        :param name: The name of the permission to search for.
        :return: The permission instance if found, None otherwise.
        """
        return self.dbSession.query(Permission).filter(Permission.name == name).first()

    def getOrCreatePermission(self, name: str, description: t.Optional[str] = None) -> Permission:
        """
        Get a permission by its name or create it if it does not exist.

        :param name: The name of the permission to search for.
        :param description: A description of the permission.
        :return: The permission instance.
        """
        permission = self.getPermissionByName(name)
        if not permission:
            permission = self.createPermission(name, description)
        return permission

    def hasPermission(self, user: User, permission: Permission) -> bool:
        """
        Check if a user has a specific permission, considering explicit deny and implicit deny.

        :param user: The user profile to check.
        :param permission: The permission to check against the user.
        :return: True if the user has the permission, False otherwise.
        """
        roleExplisitDeny = self.dbSession.query(RolePermission.permission_id).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == False
        ).filter(
            Permission.id == permission.id
        ).first()
        logger.debug(f"Checking if user {user.id} has Role permission {permission.name}: {roleExplisitDeny=}")
        if roleExplisitDeny is not None:
            return False

        userExplisitDeny = self.dbSession.query(UserPermission.permission_id).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == False
        ).filter(
            Permission.id == permission.id
        ).first()
        logger.debug(f"Checking if user {user.id} has User permission {permission.name}: {userExplisitDeny=}")
        if userExplisitDeny is not None:
            return False

        rolePermissionAllow = self.dbSession.query(RolePermission.permission_id).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == True
        ).filter(
            Permission.id == permission.id
        ).first()
        logger.debug(f"Checking if user {user.id} has Role permission {permission.name}: {rolePermissionAllow=}")

        userPermissionAllow = self.dbSession.query(UserPermission.permission_id).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == True
        ).filter(
            Permission.id == permission.id
        ).first()
        logger.debug(f"Checking if user {user.id} has User permission {permission.name}: {userPermissionAllow=}")

        return rolePermissionAllow is not None or userPermissionAllow is not None
