import typing as t

from ..Base import ServiceBase

from ...ApplicationModel import (
    Role,
    Permission,
    RolePermission,
)


class RolePermissionService(ServiceBase):
    def getAssociation(self, role: Role, permission: Permission) -> t.Optional[RolePermission]:
        """
        Get the association between a role and a permission.

        :param role: The role.
        :param permission: The permission.
        :return: The RolePermission instance or None if not found.
        """
        return self.dbSession.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        ).first()

    def createAssociation(self, role: Role, permission: Permission, effect: bool = True) -> RolePermission:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RolePermission instance.
        """
        instance = RolePermission(role=role, permission=permission, effect=effect)
        self.dbSession.add(instance)
        return instance

    def getOrCreateAssociation(self, role: Role, permission: Permission, effect: bool = True) -> RolePermission:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RolePermission instance.
        """
        association = self.getAssociation(role, permission)
        if association:
            return association
        return self.createAssociation(role, permission, effect)
