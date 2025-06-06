import typing as t

from ..base import ServiceBase

from ...ApplicationModel import (
    Role,
    Permission,
    RolePermission,
)


class RolePermissionService(ServiceBase):
    def getRolePermissionAssociation(self, role: Role, permission: Permission) -> t.Optional[RolePermission]:
        """
        Check if a role has a specific permission.

        :param role: The role to check.
        :param permission: The permission to check against the role.
        :return: True if the role has the permission, False otherwise.
        """
        return self.dbSession.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        ).first()

    def createRolePermissionAssociation(self, role: Role, permission: Permission, effect: bool = True) -> RolePermission:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RolePermission instance.
        """
        association = self.getRolePermissionAssociation(role, permission)
        if association:
            return association
        instance = RolePermission(role=role, permission=permission, effect=effect)
        self.dbSession.add(instance)
        return instance
