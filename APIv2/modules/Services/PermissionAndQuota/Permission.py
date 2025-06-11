import typing as t

from ..Base import ServiceBase
from ...ApplicationModel import (
    User,
    Permission,
    UserPermission,
    RolePermission,
)


class PermissionService(ServiceBase):
    def createPermission(self, actionId: int, description: t.Optional[str] = None) -> Permission:
        """
        Create a new permission.

        :param name: The name of the permission.
        :param description: A description of the permission.
        :return: The created permission instance.
        """
        instance = Permission(actionId=actionId, description=description)
        self.dbSession.add(instance)
        return instance

    def getPermission(self, actionId: int) -> t.Optional[Permission]:
        """
        Get a permission by its name.

        :param name: The name of the permission to search for.
        :return: The permission instance if found, None otherwise.
        """
        return self.dbSession.query(Permission).filter(Permission.actionId == actionId).first()

    def getOrCreatePermission(self, actionId: int, description: t.Optional[str] = None) -> Permission:
        """
        Get a permission by its name or create it if it does not exist.

        :param name: The name of the permission to search for.
        :param description: A description of the permission.
        :return: The permission instance.
        """
        permission = self.getPermission(actionId=actionId)
        if not permission:
            permission = self.createPermission(actionId=actionId, description=description)
        return permission

    def hasPermission(self, user: User, permission: Permission) -> bool:
        """
        Check if a user has a specific permission, considering explicit deny and implicit deny.

        :param user: The user profile to check.
        :param permission: The permission to check against the user.F
        :return: True if the user has the permission, False otherwise.
        """
        roleExplisitDeny = self.dbSession.query(RolePermission.permission_id).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == False
        ).filter(
            Permission.id == permission.id
        ).first()
        if roleExplisitDeny is not None:
            return False
        userExplisitDeny = self.dbSession.query(UserPermission.permission_id).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == False
        ).filter(
            Permission.id == permission.id
        ).first()
        if userExplisitDeny is not None:
            return False
        rolePermissionAllow = self.dbSession.query(RolePermission.permission_id).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == True
        ).filter(
            Permission.id == permission.id
        ).first()
        userPermissionAllow = self.dbSession.query(UserPermission.permission_id).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == True
        ).filter(
            Permission.id == permission.id
        ).first()
        return rolePermissionAllow is not None or userPermissionAllow is not None
