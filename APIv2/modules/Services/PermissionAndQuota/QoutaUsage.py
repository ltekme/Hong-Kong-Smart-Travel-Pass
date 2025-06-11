import datetime
from ..Base import ServiceBase

from ...ApplicationModel import (
    User,
    UserQuota,
    Quota,
    QuotaUsage,
)


class QuotaUsageService(ServiceBase):
    def getUserQuotaUsage(self, user: User, quota: Quota) -> QuotaUsage:
        """
        Get the current quota usage for a specific user and quota name.

        :param user: The user profile to check.
        :param quota: The quota to check against the user.
        :return: The current usage of the quota.
        """
        quotaUsage = self.dbSession.query(QuotaUsage).filter(
            QuotaUsage.user_id == user.id,
            UserQuota.quota_id == quota.id
        ).first()
        if not quotaUsage:
            quotaUsage = QuotaUsage(user=user, quota=quota, usage=0)
            self.dbSession.add(quotaUsage)
        return quotaUsage

    def atLimit(self, user: User, quota: Quota) -> bool:
        """
        Check if the user has reached the limit for a specific quota.

        :param user: The user profile to check.
        :param quota: The quota to check against the user.
        :return: True if the user has reached the limit, False otherwise.
        """
        quotaUsage = self.getUserQuotaUsage(user, quota)
        currentTime = datetime.datetime.now(datetime.UTC)
        lastReset = quotaUsage.lastReset.replace(tzinfo=datetime.UTC)
        if (currentTime - lastReset).total_seconds() > quota.resetPeriod:
            quotaUsage.currentValue = 0
            quotaUsage.lastReset = currentTime
            return False
        return quotaUsage.currentValue >= quota.quotaValue

    def incrementQuotaUsage(self, user: User, quota: Quota, increment: int = 1) -> None:
        """
        Increment the quota usage for a specific user and quota.

        :param user: The user profile to increment the quota usage for.
        :param quota: The quota to increment the usage for.
        :param increment: The amount to increment the usage by.
        :return: The updated quota usage instance.
        """
        self.dbSession.query(QuotaUsage).filter(
            QuotaUsage.user_id == user.id,
            QuotaUsage.quota_id == quota.id
        ).update({QuotaUsage.currentValue: QuotaUsage.currentValue + increment})
