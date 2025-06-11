import typing as t

from ..Base import ServiceBase
from ...ApplicationModel import Role
from ..PermissionAndQuota.Permission import PermissionService
from ..PermissionAndQuota.RolePermission import RolePermissionService
from ..PermissionAndQuota.Quota import QuotaService
from ..PermissionAndQuota.RoleQuota import RoleQoutaService
from ..ServiceDefination import (
    ServiceActionDefination,
    CHATLLM_CREATE,
    CHATLLM_INVOKE,
)

import sqlalchemy.orm as so


class RoleService(ServiceBase):
    def __init__(self,
                 dbSession: so.Session,
                 permissionService: PermissionService,
                 rolePermissionService: RolePermissionService,
                 qoutaService: QuotaService,
                 roleQuotaService: RoleQoutaService
                 ) -> None:
        super().__init__(dbSession)
        self.permissionService = permissionService
        self.rolePermissionService = rolePermissionService
        self.qoutaService = qoutaService
        self.roleQuotaService = roleQuotaService

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
        defaultActionNames = [
            CHATLLM_CREATE,
            CHATLLM_INVOKE,
        ]
        defaultAnonymousActionIds = list(map(lambda aName: ServiceActionDefination.getId(aName), defaultActionNames))
        role = self.getOrCreateRole(name="Anonymous", description="Role for anonymous users")
        if not role.permissions:
            # Assign default permissions to the anonymous role if not already assigned
            defaultRolePermission = list(map(lambda aId: self.permissionService.getOrCreatePermission(aId), defaultAnonymousActionIds))
            for permission in defaultRolePermission:
                self.rolePermissionService.getOrCreateAssociation(
                    role=role,
                    permission=permission,
                    effect=True
                )
        if not role.quotas:
            # Assign default quota to the anonymous role if not already assigned
            defaultRoleQuotas = list(map(lambda aId: self.qoutaService.getOrCreateQuotaByName(
                name=f"Anonymous-{aId}",
                actionId=aId,
                quotaValue=5,
                resetPeriod=1 * 60 * 24,  # Daily reset
            ), defaultAnonymousActionIds))
            for quota in defaultRoleQuotas:
                self.roleQuotaService.getOrCreateAsociation(role=role, quota=quota)
        return role
