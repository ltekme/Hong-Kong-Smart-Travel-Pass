# Importing to extend exisiting table
# No Cross Refernece between tables should be defined
# I don't think this is recommended but it works
# The Mappings here should never have any effect on data in from ChatLLMv2
# All mappings here is seperate from ChatLLMv2 as ChatLLMv2 is a seperate core component that can work on it own.
# PS: There is virtually zero typing on facebook Graph API, might as well write raw requests
import uuid
import logging
import hashlib
import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import TableBase
from . import FacebookClient

logger = logging.getLogger(__name__)


class FacebookUserIdentifyExeception(Exception):
    pass


class UserProfile(TableBase):
    """Represents a user profile."""
    __tablename__ = "user_profile"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    facebookId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, index=True, unique=True)
    personalizationSummory: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)
    personalizationSummoryLastUpdate: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime, nullable=True)
    chatRecordIds: so.Mapped[t.List["UserProifileChatRecords"]] = so.relationship(back_populates="profile")
    sessions: so.Mapped[t.List["UserProfileSession"]] = so.relationship(back_populates="profile")

    def __init__(self, username: str, facebookId: int):
        """
        Initialize a UserProfile instance.

        :param username: The username of the facebook user.
        :param messages: The facebook id of the user.
        """
        self.username = username
        self.facebookId = facebookId

    @classmethod
    def fromFacebookAccessToken(cls, accessToken: str, dbSession: so.Session) -> "UserProfile":
        """
        Initialize UserProfile instance from facebook access token.

        :param accessToken: The access token of a given facebook user.

        :return: A new instance of UserProfile with Id and username populated.
        """
        logger.debug(f"Initializing user instance from facebook access key")
        try:
            logger.debug(f"performing lookup for facebook user")
            facebookProfile = FacebookClient.getUsernameAndId(accessToken=accessToken)
            instance = cls(
                username=facebookProfile.username,
                facebookId=facebookProfile.id
            )
        except Exception as e:
            logger.error(f"Error performing user identification, {e}")
            raise FacebookUserIdentifyExeception("Error performing facebook user identification")

        try:
            logger.debug(f"Looking for user in database: {instance.facebookId}({instance.username})")
            instanceInDb = dbSession.query(cls).where(cls.facebookId == instance.facebookId).first()
            if instanceInDb is not None:
                logger.debug(f"Found user in database: {instance.facebookId}({instance.username})")
                return instanceInDb
        except Exception as e:
            logger.error(f"Error performing user lookup in db, {e}")
            raise Exception("Error looking up user in database")

        try:
            logger.debug(f"User: {instance.facebookId} ({instance.username}) was not found in database, creating")
            dbSession.add(instance)
            dbSession.commit()
            return instance
        except Exception as e:
            logger.error(f"Error creating user, {e}")
            raise Exception("Error creating user profile")


class UserProifileChatRecords(TableBase):
    """Represents a semi key-value pair of user profile and chat records."""
    __tablename__ = "user_proifile_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="chatRecordIds")
    chatId: so.Mapped[str] = so.mapped_column(sa.ForeignKey(f"chats.chatId"), nullable=True)


class UserProfileSession(TableBase):
    """Used to store temporary access to user profiles"""
    __tablename__ = "user_proifile_sessions"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="sessions")
    sessionToken: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    expire: so.Mapped[datetime.datetime] = so.mapped_column(sa.DateTime, nullable=False)

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

    @classmethod
    def create(cls, profile: UserProfile, expire: datetime.datetime, dbSession: so.Session) -> "UserProfileSession":
        """
        Creates a new UserProfileSessions instance.

        :param profile: The user profile associated with the session.
        :param expire: The expiration datetime of the session.

        :return: A new instance of UserProfileSessions with the provided profile and expiration.
        """
        try:
            logger.debug(f"Initializing session from user profile: {profile.facebookId}")
            instance = cls(
                profile=profile,
                expire=expire,
                sessionToken=hashlib.md5(f"{profile.facebookId}{str(uuid.uuid4())}".encode()).hexdigest(),
            )
        except Exception as e:
            logger.error(e)
            raise Exception("Session Creation Failed")

        try:
            logger.debug(f"Writing session data for: {profile.facebookId=}, {instance.sessionToken[:5]=}")
            dbSession.add(instance)
            dbSession.commit()
            return instance
        except Exception as e:
            logger.error(f"Error creating session for user {profile.facebookId=}, {e}")
            raise Exception("Error creating user session")
