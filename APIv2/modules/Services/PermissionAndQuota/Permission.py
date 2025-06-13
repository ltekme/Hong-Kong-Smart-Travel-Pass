import typing as t

from ..Base import ServiceBase
from ...ApplicationModel import (
    User,
    Role,
    Permission,
    UserPermission,
    RolePermission,
)


class NoPermssionError(Exception):
    def __init__(self, action: str, message: t.Optional[str] = None) -> None:
        super().__init__(message)
        self.action = action


class PermissionService(ServiceBase):

    def __init__(self, dbSession: t.Any) -> None:
        super().__init__(dbSession, serviceName="PermissionService")

    def createPermission(self, actionId: int, description: t.Optional[str] = None) -> Permission:
        """
        Create a new permission.

        :param name: The name of the permission.
        :param description: A description of the permission.
        :return: The created permission instance.
        """
        self.loggerDebug(f"Creating permission with actionId: {actionId}, description: {description}")
        instance = Permission(actionId=actionId, description=description)
        self.dbSession.add(instance)
        return instance

    def getPermission(self, actionId: int) -> t.Optional[Permission]:
        """
        Get a permission by its name.

        :param name: The name of the permission to search for.
        :return: The permission instance if found, None otherwise.
        """
        self.loggerDebug(f"Getting permission with actionId: {actionId}")
        return self.dbSession.query(Permission).filter(Permission.actionId == actionId).first()

    def getOrCreatePermission(self, actionId: int, description: t.Optional[str] = None) -> Permission:
        """
        Get a permission by its name or create it if it does not exist.

        :param name: The name of the permission to search for.
        :param description: A description of the permission.
        :return: The permission instance.
        """
        self.loggerDebug(f"Getting or creating permission with actionId: {actionId}, description: {description}")
        permission = self.getPermission(actionId=actionId)
        if not permission:
            self.loggerDebug(f"Permission with actionId: {actionId} not found, creating new one.")
            permission = self.createPermission(actionId=actionId, description=description)
        return permission

    def hasPermission(self, user: User, permission: Permission) -> bool:
        """
        Check if a user has a specific permission, considering explicit deny and implicit deny.

        :param user: The user profile to check.
        :param permission: The permission to check against the user.F
        :return: True if the user has the permission, False otherwise.
        """
        self.loggerDebug(f"Checking if user: {user.id} roles has permission: {permission.actionId}")
        roleExplisitDeny = self.dbSession.query(RolePermission.permission_id).join(
            Permission, RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == False,
            Permission.id == permission.id
        ).first()
        if roleExplisitDeny is not None:
            self.loggerDebug(f"User: {user.id} has roles explicit deny for permission: {permission.actionId}")
            return False

        self.loggerDebug(f"User: {user.id} does not have explicit role deny for permission: {permission.actionId}")
        self.loggerDebug(f"Checking if user: {user.id} has explicit deny for permission: {permission.actionId}")
        userExplisitDeny = self.dbSession.query(UserPermission.permission_id).join(
            Permission, UserPermission.permission_id == Permission.id
        ).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == False,
            Permission.id == permission.id
        ).first()
        if userExplisitDeny is not None:
            self.loggerDebug(f"User: {user.id} has explicit deny for permission: {permission.actionId}")
            return False

        self.loggerDebug(f"User: {user.id} does not have explicit deny for permission: {permission.actionId}")

        rolePermissionAllow = self.dbSession.query(RolePermission.permission_id).join(
            Permission, RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id.in_([r.id for r in user.roles]),
            RolePermission.effect == True,
            Permission.id == permission.id
        ).first()
        userPermissionAllow = self.dbSession.query(UserPermission.permission_id).join(
            Permission, UserPermission.permission_id == Permission.id
        ).filter(
            UserPermission.user_id == user.id,
            UserPermission.effect == True,
            Permission.id == permission.id
        ).first()

        self.loggerDebug(f"User: {user.id} role permission allow: {rolePermissionAllow is not None}, user permission allow: {userPermissionAllow is not None}")
        return rolePermissionAllow is not None or userPermissionAllow is not None

    def getRoleAssociation(self, role: Role, permission: Permission) -> t.Optional[RolePermission]:
        """
        Get the association between a role and a permission.

        :param role: The role.
        :param permission: The permission.
        :return: The RolePermission instance or None if not found.
        """
        self.loggerDebug(f"Getting role permission association for role: {role.id}, permission: {permission.id}")
        return self.dbSession.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        ).first()

    def createRoleAssociation(self, role: Role, permission: Permission, effect: bool = True) -> RolePermission:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RolePermission instance.
        """
        self.loggerDebug(f"Creating role permission association for role: {role.id}, permission: {permission.id}, effect: {effect}")
        instance = RolePermission(role=role, permission=permission, effect=effect)
        self.dbSession.add(instance)
        return instance

    def getOrCreateRoleAssociation(self, role: Role, permission: Permission, effect: bool = True) -> RolePermission:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RolePermission instance.
        """
        self.loggerDebug(f"Getting or creating role permission association for role: {role.id}, permission: {permission.id}, effect: {effect}")
        association = self.getRoleAssociation(role, permission)
        if association:
            self.loggerDebug(f"Role permission association already exists for role: {role.id}, permission: {permission.id}, effect: {association.effect}")
            return association
        self.loggerDebug(f"Role permission association does not exist for role: {role.id}, permission: {permission.id}, creating new one.")
        return self.createRoleAssociation(role, permission, effect)
