# Importing to extend exisiting table
# No Cross Refernece between tables should be defined
# I don't think this is recommended but it works
# The Mappings here should never have any effect on data in from ChatLLMv2
# All mappings here is seperate from ChatLLMv2 as ChatLLMv2 is a seperate core component that can work on it own.
# PS: There is virtually zero typing on facebook Graph API, might as well write raw requests

import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy.sql as sl

from ChatLLMv2.DataHandler import TableBase


class SocialsProfileProvider(TableBase):
    """
    Represents a social profile provider 

    SocialsProfileProvider class represents a social idnetifer provider.
    e.g. Facebook, Google SSO, X(Twitter)
    """
    __tablename__ = "socials_provider"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True)
    socials: so.Mapped[t.List["UserSocialProfile"]] = so.relationship(back_populates="provider")

    def __init__(self, name: str):
        """
        Initialize a SocialsProfileProvider instance.

        :param name: The name of the provider.
        """
        self.name = name


class UserSocialProfile(TableBase):
    """
    Represents a social profile

    This class represents the mapping of user and their social media profiles
    """
    __tablename__ = "user_socials"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    socialId: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    socialName: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)
    socialProfileSummory: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)
    lastUpdate: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), default=sl.func.now())

    user_id: so.Mapped[t.Optional[str]] = so.mapped_column(sa.ForeignKey("user.id"), nullable=True)
    user: so.Mapped[t.Optional["User"]] = so.relationship(back_populates="socials")
    provider_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("socials_provider.id"), nullable=False)
    provider: so.Mapped["SocialsProfileProvider"] = so.relationship(back_populates="socials")

    def __init__(self, socialId: str, provider: SocialsProfileProvider) -> None:
        """
        Initialize a UserSocialRecord instance.

        :param socialId: The socialId of the user.
        :param name: The profileId of the socials.
        """
        self.socialId = socialId
        self.provider = provider


class RoleQuota(TableBase):
    __tablename__ = "role_quota"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    roleId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("role.id"), nullable=False)

    actionId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    value: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    resetInterval: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=60 * 60 * 24)
    description: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint('roleId', 'actionId', name='uq_role_action'),
    )


class UserQuota(TableBase):
    __tablename__ = "user_quota"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    userId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=False)

    actionId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    value: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    resetInterval: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=60 * 60 * 24)
    description: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint('userId', 'actionId', name='uq_user_action'),
    )


class QuotaUsage(TableBase):
    """
    Represents the usage of a quota by a user.

    This class is used to track the usage of a quota by a user.
    It is used to track the current value of the quota and the last time it was reset.
    """
    __tablename__ = "quota_usage"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    userId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    actionId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)

    value: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    lastReset: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False, default=sl.func.now())


class Permission(TableBase):
    """"
    Represents a permission.

    actionId: The ID of the service action that this permission applies to. Ref: ServiceDefination.py

    """
    __tablename__ = "permission"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    description: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)
    actionId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)

    roles: so.Mapped[t.List["Role"]] = so.relationship("Role", secondary="role_permission_association", back_populates="permissions")
    users: so.Mapped[t.List["User"]] = so.relationship("User", secondary="user_permission_association", back_populates="permissions")

    def __init__(self, actionId: int, description: t.Optional[str] = None) -> None:
        """
        Initialize a Permission instance.

        :param serviceAction: The service action that this permission applies to.
        :param description: A description of the permission.
        """
        self.actionId = actionId
        self.description = description


class RolePermission(TableBase):
    """Represents the many-to-many relationship between roles and permissions."""
    __tablename__ = "role_permission_association"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("role.id"))
    permission_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("permission.id"))
    effect: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, default=False)

    def __init__(self, role: "Role", permission: Permission, effect: bool = True) -> None:
        """
        Initialize a RolePermission instance.

        :param role_id: The ID of the role.
        :param permission_id: The ID of the permission.
        :param effect: Whether the permission is granted (True) or denied (False).
        """
        self.role_id = role.id
        self.permission_id = permission.id
        self.effect = effect


class UserPermission(TableBase):
    """Represents the many-to-many relationship between users and permissions."""
    __tablename__ = "user_permission_association"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    permission_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("permission.id"))
    effect: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, default=False)


class Role(TableBase):
    """Represents a user role."""
    __tablename__ = "role"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True, index=True)
    description: so.Mapped[t.Optional[str]] = so.mapped_column(sa.String, nullable=True)

    permissions: so.Mapped[t.List["Permission"]] = so.relationship("Permission", secondary="role_permission_association", back_populates="roles")
    users: so.Mapped[t.List["User"]] = so.relationship("User", secondary="user_role_association", back_populates="roles")

    def __init__(self, name: str, description: t.Optional[str] = None) -> None:
        """
        Initialize a Role instance.

        :param name: The name of the user role.
        :param description: A description of the user role.
        """
        self.name = name
        self.description = description


class UserRole(TableBase):
    """Represents the many-to-many relationship between users and roles."""
    __tablename__ = "user_role_association"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("role.id"))

    def __init__(self, user: "User", role: Role) -> None:
        """
        Initialize a UserRole instance.

        :param user: The user instance.
        :param role: The role instance.
        """
        self.user_id = user.id
        self.role_id = role.id


class User(TableBase):
    """Represents a user profile."""
    __tablename__ = "user"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    public: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=True, default=False)

    chatRecordIds: so.Mapped[t.List["UserChatRecord"]] = so.relationship(back_populates="user")
    sessions: so.Mapped[t.List["UserSession"]] = so.relationship(back_populates="user")
    socials: so.Mapped[t.List["UserSocialProfile"]] = so.relationship(back_populates="user")

    roles: so.Mapped[t.List["Role"]] = so.relationship("Role", secondary="user_role_association", back_populates="users")
    permissions: so.Mapped[t.List["Permission"]] = so.relationship("Permission", secondary="user_permission_association", back_populates="users")

    def __init__(self, username: str) -> None:
        """
        Initialize a User instance.

        :param username: The username of the user.
        """
        self.username = username


class UserChatRecord(TableBase):
    """Represents a semi key-value pair of user profile and chat records."""
    __tablename__ = "user_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chatId: so.Mapped[str] = so.mapped_column(sa.ForeignKey("chats.chatId"), index=True, nullable=False)
    summory: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True, nullable=False)
    user: so.Mapped["User"] = so.relationship(back_populates="chatRecordIds")

    def __init__(self, chatId: str, user: User) -> None:
        """
        Initialize a User instance.

        :param chatId: The chatId.
        :param User: The User Profile.

        :return: None.
        """
        self.chatId = chatId
        self.user_id = user.id

    def editSummory(self, newSummory: str, dbSession: so.Session) -> None:
        """
        Edit summory of this chat

        :param newSummory: The summory.

        :param dbSession: The dbSession to make the query.
        """
        self.summory = newSummory
        dbSession.commit()


class UserSession(TableBase):
    """Used to store temporary access to user profiles"""
    __tablename__ = "user_sessions"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    user: so.Mapped["User"] = so.relationship(back_populates="sessions")
    sessionToken: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, index=True)
    expire: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)

    def __init__(self, user: User, sessionToken: str, expire: datetime.datetime):
        """
        Initialize a User instance.

        :param profile: The User instance that the session belong to.
        :param sessionToken: The session identifer, used as a temporary key to access the user profile.
        :param expire: The datetime instance of when this session Id expire
        """
        self.user = user
        self.sessionToken = sessionToken
        self.expire = expire
