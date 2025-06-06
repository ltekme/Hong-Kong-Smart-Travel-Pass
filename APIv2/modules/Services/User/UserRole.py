import typing as t

from ..base import ServiceBase

from ...ApplicationModel import (
    User,
    Role,
    UserRole,
)


class UserRoleService(ServiceBase):
    def getUserRoleAssociation(self, user: User, role: Role) -> t.Optional[UserRole]:
        """
        Get the association between a user and a role.
        :param user: The user.
        :param role: The role.
        :return: The association instance or None if not found.
        """
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
        association = self.getUserRoleAssociation(user, role)
        if not association:
            association = UserRole(user=user, role=role)
            self.dbSession.add(association)
        return association
