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
    __tablename__ = "user_profile_socials"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    socialId: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    profileSummory: so.Mapped[str | None] = so.mapped_column(sa.String, nullable=True)
    lastUpdate: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), default=sl.func.now())

    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="socials")
    provider_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("socials_provider.id"))
    provider: so.Mapped["SocialsProfileProvider"] = so.relationship(back_populates="socials")

    def __init__(self, profileId: str, provider: SocialsProfileProvider) -> None:
        """
        Initialize a UserProfileSocialRecord instance.

        :param name: The profileId of the socials.
        """
        self.profileId = profileId
        self.provider = provider


class UserProfile(TableBase):
    """Represents a user profile."""
    __tablename__ = "user_profile"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    public: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=True, default=False)
    chatRecordIds: so.Mapped[t.List["UserChatRecord"]] = so.relationship(back_populates="profile")
    sessions: so.Mapped[t.List["UserSession"]] = so.relationship(back_populates="profile")
    socials: so.Mapped[t.List["UserSocialProfile"]] = so.relationship(back_populates="profile")

    def __init__(self, username: str):
        """
        Initialize a UserProfile instance.

        :param username: The username of the user.
        """
        self.username = username


class UserChatRecord(TableBase):
    """Represents a semi key-value pair of user profile and chat records."""
    __tablename__ = "user_proifile_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"), index=True, nullable=False)
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="chatRecordIds")
    chatId: so.Mapped[str] = so.mapped_column(sa.ForeignKey(f"chats.chatId"), index=True, nullable=False)
    summory: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)

    def __init__(self, chatId: str, userProfile: UserProfile) -> None:
        """
        Initialize a UserProfile instance.

        :param chatId: The chatId.
        :param userProfile: The User Profile.

        :return: None.
        """
        self.chatId = chatId
        self.profile = userProfile

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
    __tablename__ = "user_proifile_sessions"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="sessions")
    sessionToken: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, index=True)
    expire: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)

    def __init__(self, profile: UserProfile, sessionToken: str, expire: datetime.datetime):
        """
        Initialize a UserProfile instance.

        :param profile: The UserProfile instance that the session belong to.
        :param sessionToken: The session identifer, used as a temporary key to access the user profile.
        :param expire: The datetime instance of when this session Id expire
        """
        self.profile = profile
        self.sessionToken = sessionToken
        self.expire = expire
