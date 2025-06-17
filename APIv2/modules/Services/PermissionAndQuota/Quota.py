import typing as t
import datetime as dt

from ..Base import ServiceBase

from APIv2.modules.ApplicationModel import User
from APIv2.modules.ApplicationModel import Role
from APIv2.modules.ApplicationModel import UserQuota
from APIv2.modules.ApplicationModel import RoleQuota
from APIv2.modules.ApplicationModel import QuotaUsage


class QuotaService(ServiceBase):

    def __init__(self, dbSession: t.Any) -> None:
        super().__init__(dbSession, serviceName="QuotaService")

    def getUserQuota(self, users: list[User], actionIds: list[int], limit: int = 1) -> list[UserQuota]:
        """
        Get the user's quota for a specific actionId.

        :param users: List of User instances to check.
        :param actionIds: List of action IDs to check against the user's quota.
        :return: The UserQuota instance or None if not found.
        """
        self.loggerDebug(f"Getting user quota for users: {[user.id for user in users]}, actionIds: {actionIds}")
        return self.dbSession.query(UserQuota).filter(
            UserQuota.userId.in_([r.id for r in users]),
            UserQuota.actionId.in_(actionIds)
        ).limit(limit).all()

    def getRoleQuota(self, roles: list[Role], actionIds: list[int], limit: int = 1) -> list[RoleQuota]:
        """
        Get the role quota for a specific role and actionId.

        :param roles: List of Role instances to check.
        :param actionIds: List of action IDs to check against the user's quota.
        :return: The RoleQuota instance or None if not found.
        """
        self.loggerDebug(f"Getting role quota for roles: {[role.id for role in roles]}, actionIds: {actionIds}")
        return self.dbSession.query(RoleQuota).filter(
            RoleQuota.roleId.in_([r.id for r in roles]),
            RoleQuota.actionId.in_(actionIds)
        ).limit(limit).all()

    def getRolesMaxQuota(self, roleIds: list[int], actionId: int) -> t.Optional[RoleQuota]:
        """
        Get the maximum quota for a list of role IDs and actionId.

        :param roleIds: List of role IDs to check.
        :param actionId: The action ID to check against the roles' quota.
        :return: The RoleQuota instance or None if not found.
        """
        self.loggerDebug(f"Getting max role quota for roleIds: {roleIds}, actionId: {actionId}")
        return self.dbSession.query(RoleQuota).filter(
            RoleQuota.roleId.in_(roleIds),
            RoleQuota.actionId == actionId
        ).order_by(RoleQuota.value.desc()).limit(1).first()

    def getQuotaUsage(self, user: User, actionId: int) -> t.Optional[QuotaUsage]:
        """
        Get the quota usage for a specific user and actionId.

        :param user: The user profile to check.
        :param actionId: The action ID to check against the user's quota usage.
        :return: The QuotaUsage instance or None if not found.
        """
        self.loggerDebug(f"Getting quota usage for user: {user.id}, actionId: {actionId}")
        return self.dbSession.query(QuotaUsage).filter(
            QuotaUsage.userId == user.id,
            QuotaUsage.actionId == actionId
        ).first()

    def createQuotaUsage(self, user: User, actionId: int, value: int = 0, lastReset: t.Optional[dt.datetime] = dt.datetime.now(dt.UTC)) -> QuotaUsage:
        """
        Create a new quota usage record for a user and actionId.

        :param user: The user profile to create the quota usage for.
        :param actionId: The action ID to associate with the quota usage.
        :param value: The initial value of the quota usage.
        :param lastReset: The last reset datetime for the quota usage.
        :return: The created QuotaUsage instance.
        """
        self.loggerDebug(f"Creating quota usage for user: {user.id}, actionId: {actionId}, value: {value}, lastReset: {lastReset}")
        instance = QuotaUsage(userId=user.id, actionId=actionId, value=value, lastReset=lastReset)
        self.dbSession.add(instance)
        return instance

    def getOrCreateQuotaUsage(self, user: User, actionId: int, value: int = 0, lastReset: t.Optional[dt.datetime] = None) -> QuotaUsage:
        """
        Get or create a quota usage record for a user and actionId.

        :param user: The user profile to check or create the quota usage for.
        :param actionId: The action ID to associate with the quota usage.
        :param value: The initial value of the quota usage.
        :param lastReset: The last reset datetime for the quota usage.
        :return: The QuotaUsage instance.
        """
        self.loggerDebug(f"Getting or creating quota usage for user: {user.id}, actionId: {actionId}")
        usage = self.getQuotaUsage(user, actionId)
        if not usage:
            self.loggerDebug(f"Quota usage for user: {user.id}, actionId: {actionId} not found, creating new one.")
            usage = self.createQuotaUsage(user=user, actionId=actionId, value=value, lastReset=lastReset)
        return usage

    def userHasQuotaRemaining(self, user: User, actionId: int) -> bool:
        """
        Check if a user has remaining quota for a specific actionId.

        :param user: The user profile to check.
        :param actionId: The action ID to check against the user's quota.
        :return: True if the user has remaining quota, False otherwise.
        """
        self.loggerDebug(f"Checking if user: {user.id} has quota remaining for actionId: {actionId}")
        currentDatetime = dt.datetime.now(dt.UTC)
        usage = self.getOrCreateQuotaUsage(user, actionId)
        self.loggerDebug(f"Current usage for user: {user.id}, actionId: {actionId} is {usage.value}, last reset at {usage.lastReset}")
        userQuota = self.getUserQuota([user], [actionId])
        if userQuota and userQuota[0].value > 0:
            self.loggerDebug(f"User quota for user: {user.id}, actionId: {actionId} is {userQuota[0].value}")
            if userQuota[0].value == 0:
                return False
            if usage.value < userQuota[0].value:
                return True
            self.loggerDebug(f"Checking if quota needs reset for user: {user.id}, actionId: {actionId}")
            if self.quotaNeedReset(usage.lastReset, userQuota[0].resetInterval):
                self.loggerDebug(f"Resetting quota usage for user: {user.id}, actionId: {actionId}")
                self.resetQuotaUsage(usage, currentDatetime)
                return True

        self.loggerDebug(f"Checking role quotas for user: {user.id}, actionId: {actionId}")
        maxUserRoleQuota = self.getRolesMaxQuota(list(map(lambda x: x.id, user.roles)), actionId)
        if maxUserRoleQuota and maxUserRoleQuota.value > 0:
            self.loggerDebug(f"Max role quota for user: {user.id}, actionId: {actionId} is {maxUserRoleQuota.value}")
            if maxUserRoleQuota.value == 0:
                return False
            if usage.value < maxUserRoleQuota.value:
                return True
            self.loggerDebug(f"Checking if quota needs reset for user: {user.id}, actionId: {actionId} with role quota")
            if self.quotaNeedReset(usage.lastReset, maxUserRoleQuota.resetInterval):
                self.loggerDebug(f"Resetting quota usage for user: {user.id}, actionId: {actionId} with role quota")
                self.resetQuotaUsage(usage, currentDatetime)
                return True

        self.loggerDebug(f"User: {user.id} does not have remaining quota for actionId: {actionId}")
        return False

    def quotaNeedReset(self, lastReset: dt.datetime, resetInterval: int) -> bool:
        """
        Check if the quota usage needs to be reset based on the last reset time and reset interval.

        :param lastReset: The last reset datetime.
        :param resetInterval: The reset interval in seconds.
        :return: True if the usage needs to be reset, False otherwise.
        """
        return (dt.datetime.now(dt.UTC) - lastReset.replace(tzinfo=dt.UTC)).seconds > resetInterval

    def resetQuotaUsage(self, quotaUsage: QuotaUsage, lastReset: dt.datetime = dt.datetime.now(dt.UTC)) -> QuotaUsage:
        """
        Reset the quota usage for a specific QuotaUsage instance.

        :param quotaUsage: The QuotaUsage instance to reset.
        :return: The updated QuotaUsage instance with usage reset to 0.
        """
        self.loggerDebug(f"Resetting quota usage for user: {quotaUsage.userId}, actionId: {quotaUsage.actionId}")
        quotaUsage.value = 0
        quotaUsage.lastReset = lastReset
        return quotaUsage

    def incrementQuotaUsage(self, user: User, actionId: int, increment: int = 1) -> QuotaUsage:
        """
        Increment the quota usage for a specific user and actionId.

        :param user: The user profile to increment quota usage for.
        :param actionId: The action ID to increment quota usage against.
        :param increment: The amount to increment the usage by.
        :return: The updated QuotaUsage instance.
        """
        self.loggerDebug(f"Incrementing quota usage for user: {user.id}, actionId: {actionId} by {increment}")
        usage = self.getOrCreateQuotaUsage(user, actionId)
        usage.value += increment
        return usage

    def createRoleQuota(self, role: Role, actionId: int, value: int, resetInterval: t.Optional[int] = None) -> RoleQuota:
        """
        Create a role quota for a specific role and actionId.

        :param roleId: The ID of the role to create the quota for.
        :param actionId: The action ID to associate with the quota.
        :param value: The maximum value of the quota.
        :param resetInterval: The reset interval in seconds.
        :return: The created RoleQuota instance.
        """
        self.loggerDebug(f"Creating role quota for role: {role.id}, actionId: {actionId}, value: {value}, resetInterval: {resetInterval}")
        instance = RoleQuota(roleId=role.id, actionId=actionId, value=value, resetInterval=resetInterval)
        self.dbSession.add(instance)
        return instance

    def getOrCreateRoleQuota(self, role: Role, actionId: int, value: int, resetInterval: t.Optional[int] = None) -> RoleQuota:
        """
        Get or create a role quota for a specific role and actionId.

        :param roleId: The ID of the role to check or create the quota for.
        :param actionId: The action ID to associate with the quota.
        :param value: The maximum value of the quota.
        :param resetInterval: The reset interval in seconds.
        :return: The RoleQuota instance.
        """
        self.loggerDebug(f"Getting or creating role quota for role: {role.id}, actionId: {actionId}, value: {value}, resetInterval: {resetInterval}")
        quota = self.getRoleQuota([role], [actionId])
        if not quota:
            self.loggerDebug(f"Role quota for role: {role.id}, actionId: {actionId} not found, creating new one.")
            quota = self.createRoleQuota(role=role, actionId=actionId, value=value, resetInterval=resetInterval)

        self.loggerDebug(f"Role quota for role: {role.id}, actionId: {actionId} found or created with value: {quota[0].value if isinstance(quota, list) else quota.value}")
        return quota[0] if isinstance(quota, list) else quota
