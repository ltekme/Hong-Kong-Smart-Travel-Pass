import typing as t

from ...ApplicationModel import (
    Role,
    Quota,
    RoleQuota,
)
from ..Base import ServiceBase


class RoleQoutaService(ServiceBase):
    def getAssociation(self, role: Role, quota: Quota) -> t.Optional[RoleQuota]:
        """
        Get the association between a role and a qouta.

        :param role: The role.
        :param quota: The quota.
        :return: The RoleQuota instance or None if not found.
        """
        return self.dbSession.query(RoleQuota).filter(
            RoleQuota.role_id == role.id,
            RoleQuota.quota_id == quota.id,
        ).first()

    def createAssociation(self, role: Role, quota: Quota) -> RoleQuota:
        """
        Create a role-permission association.

        :param role: The role.
        :param permission: The permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        :return: The created RoleQuota instance.
        """
        instance = RoleQuota(role=role, quota=quota)
        self.dbSession.add(instance)
        return instance

    def getOrCreateAsociation(self, role: Role, quota: Quota) -> RoleQuota:
        """
        Create an association between a role and a quota.

        :param roleId: The ID of the role.
        :param quotaId: The ID of the quota.
        :return: The created RoleQuota instance.
        """
        association = self.getAssociation(role, quota)
        if association:
            return association
        return self.createAssociation(role, quota)
