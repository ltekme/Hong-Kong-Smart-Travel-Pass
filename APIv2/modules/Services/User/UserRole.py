import typing as t

from ...Services.Base import ServiceBase

from ...ApplicationModel import (
    User,
    Role,
    UserRole,
)


class UserRoleService(ServiceBase):
    def __init__(self, dbSession: t.Any) -> None:
        super().__init__(dbSession, serviceName="UserRoleService")

    def getUserRoleAssociation(self, user: User, role: Role) -> t.Optional[UserRole]:
        """
        Get the association between a user and a role.
        :param user: The user.
        :param role: The role.
        :return: The association instance or None if not found.
        """
        self.loggerDebug(f"Getting user role association for user: {user.id}, role: {role.id}")
        return self.dbSession.query(UserRole).filter(
            UserRole.user_id == user.id and UserRole.role_id == role.id
        ).first()

    def associateUserWithRole(self, user: User, role: Role) -> UserRole:
        """
        Associate a user with a role.
        :param user: The user to associate.
        :param role: The role to associate with the user.
        :return: The association instance.
        """
        self.loggerDebug(f"Associating user: {user.id} with role: {role.id}")
        association = self.getUserRoleAssociation(user, role)
        if not association:
            self.loggerDebug(f"Creating new association for user: {user.id}, role: {role.id}")
            association = UserRole(user=user, role=role)
            self.dbSession.add(association)
        return association
