import typing as t
import sqlalchemy.orm as so

from ..Base import ServiceBase

from ...ApplicationModel import (
    User,
    UserQuota,
    Quota,
    RoleQuota,
)

from .QoutaUsage import QuotaUsageService


class QuotaService(ServiceBase):

    def __init__(self, dbSession: so.Session, quotaUsageService: QuotaUsageService) -> None:
        super().__init__(dbSession)
        self.quotaUsageService = quotaUsageService

    def getQuotaByName(self, name: str) -> t.Optional[Quota]:
        """
        Get the quota for a specific user.

        :param userId: The ID of the user.
        :return: The quota for the user.
        """
        return self.dbSession.query(Quota).where(Quota.name == name).first()

    def createQuotaByName(self,
                          name: str,
                          actionId: int,
                          quotaValue: int,
                          resetPeriod: int = 1*60*24,
                          description: t.Optional[str] = None
                          ) -> Quota:
        """
        Create a new quota.

        :param name: The name of the quota.
        :param serviceAction: The service action associated with the quota.
        :param description: A description of the quota.
        :return: The created quota instance.
        """
        instance = Quota(
            name=name,
            actionId=actionId,
            quotaValue=quotaValue,
            resetPeriod=resetPeriod,
            description=description
        )
        self.dbSession.add(instance)
        return instance

    def getOrCreateQuotaByName(self,
                               name: str,
                               actionId: int,
                               quotaValue: int,
                               resetPeriod: int = 1*60*24,
                               description: t.Optional[str] = None
                               ) -> Quota:
        """
        Get or create a quota by its name.

        :param name: The name of the quota.
        :param serviceAction: The service action associated with the quota.
        :param description: A description of the quota.
        :return: The quota instance.
        """
        instance = self.getQuotaByName(name)
        if instance is not None:
            return instance
        return self.createQuotaByName(name, actionId, quotaValue, resetPeriod, description)

    def hasQuota(self, user: User, quota: Quota, default: bool = True) -> bool:
        """
        Check if a user has a specific quota.

        :param userId: The ID of the user.
        :param serviceAction: The service action associated with the quota.
        :return: True if the user has the quota, False otherwise.
        """
        # look if the qouta is associated with the user
        userQuota = self.dbSession.query(UserQuota).filter(
            UserQuota.user_id == user.id,
            UserQuota.quota_id == quota.id
        ).first()
        if userQuota:
            # When asssociated with the user, check if the user has reached the limit
            if self.quotaUsageService.atLimit(user, quota):
                return False
            return True

        # look if the qouta is associated with the user roles
        userRolesQoutas = self.dbSession.query(RoleQuota).filter(
            RoleQuota.role_id.in_(list(map(lambda r: r.id, user.roles))),
            RoleQuota.quota_id == quota.id
        ).first()
        if userRolesQoutas:
            # When asssociated with the user roles, check if the user has reached the limit
            if self.quotaUsageService.atLimit(user, quota):
                return False
            return True

        return default
