# Importing to extend exisiting table
# No Cross Refernece between tables should be defined
# I don't think this is recommended but it works
# The Mappings here should never have any effect on data in from ChatLLMv2
# All mappings here is seperate from ChatLLMv2 as ChatLLMv2 is a seperate core component that can work on it own.
# PS: There is virtually zero typing on facebook Graph API, might as well write raw requests
import uuid
import pytz
import hashlib
import datetime
import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import TableBase
from . import FacebookClient
from ..config import logger


class FacebookUserIdentifyExeception(Exception):
    pass


class UserProifileChatRecordsExistExeception(Exception):
    pass


class UserProfile(TableBase):
    """Represents a user profile."""
    __tablename__ = "user_profile"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    facebookId: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, index=True, unique=True)
    personalizationSummory: so.Mapped[str | None] = so.mapped_column(sa.String, nullable=True)
    personalizationSummoryLastUpdate: so.Mapped[datetime.datetime | None] = so.mapped_column(sa.DateTime, nullable=True)
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
                facebookId=facebookProfile.facebookId
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

    def updatePersonalizationSummory(self, newSummory: str, dbSession: so.Session) -> None:
        """
        Update profile personalization summory

        :param newSummory: The new profile summory
        :param dbSession: The dbSession to make the query.

        :return: None.
        """
        try:
            logger.debug(f"Updating User profile personalizationa summory for user {self.facebookId=}")
            self.personalizationSummory = newSummory
            self.personalizationSummoryLastUpdate = datetime.datetime.now()
            dbSession.commit()
        except Exception as e:
            logger.error(e)
            raise Exception(f"Error updating personalizationa summory for user {self.facebookId=}")


class UserProifileChatRecords(TableBase):
    """Represents a semi key-value pair of user profile and chat records."""
    __tablename__ = "user_proifile_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"), index=True)
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="chatRecordIds")
    chatId: so.Mapped[str] = so.mapped_column(sa.ForeignKey(f"chats.chatId"), index=True)

    def __init__(self, chatId: str, userProfile: UserProfile) -> None:
        """
        Initialize a UserProfile instance.

        :param chatId: The chatId.
        :param userProfile: The User Profile.

        :return: None.
        """
        self.chatId = chatId
        self.profile = userProfile

    @classmethod
    def getUserProfileFromChatId(cls, chatId: str, dbSession: so.Session) -> UserProfile | None:
        """
        Get associated User Profile of a chatId

        :param chatId: The chatId.
        :param dbSession: The dbSession to make the query.

        :return: A new instance of UserProfile or None.
        """
        try:
            logger.debug(f"Getting User profile of {chatId=}")
            profileRecord = dbSession.query(cls).where(cls.chatId == chatId).first()
            if profileRecord is not None:
                logger.debug(f"Found UserProfile {profileRecord=} for {chatId=}")
                return profileRecord.profile
            logger.debug(f"Record for {chatId=} not found")
            return None
        except Exception as e:
            logger.error(e)
            raise Exception("Error querying database")

    @classmethod
    def addRecord(cls, chatId: str, userProfile: UserProfile, dbSession: so.Session) -> bool:
        """
        Add chat user pair record, throw exeception if chatId is aready associated with a profile

        :param chatId: The chatId.
        :param userProfile: The User Profile.
        :param dbSession: The dbSession to make the query.

        :return: True if success
        """
        # done in application
        # try:
        #     logger.debug(f"adding chatId and user pair for {chatId=} | {userProfile.id=}")
        #     existingUserProfile = cls.getUserProfileFromChatId(chatId=chatId, dbSession=dbSession)
        #     if existingUserProfile is not None:
        #         logger.debug(f"Profile record already exists for {chatId=}")
        #         if existingUserProfile == userProfile:
        #             logger.debug(f"Profile record for {chatId=} matched, nothing to do")
        #             return True
        #         if existingUserProfile != userProfile:
        #             raise UserProifileChatRecordsExistExeception("The chatId is already associated with a profile")
        # except UserProifileChatRecordsExistExeception as e:
        #     raise UserProifileChatRecordsExistExeception(e)
        # except Exception as e:
        #     logger.error(e)
        #     Exception("Error checking UserProfileChatId pair")

        try:
            logger.debug(f"adding chatId and user pair for {chatId=} | {userProfile.id=}")
            record = cls(chatId=chatId, userProfile=userProfile)
            dbSession.add(record)
            dbSession.commit()
        except Exception as e:
            logger.error(e)
            Exception("Error creating UserProfileChatId pair")
        return True


class UserProfileSession(TableBase):
    """Used to store temporary access to user profiles"""
    __tablename__ = "user_proifile_sessions"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="sessions")
    sessionToken: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, index=True)
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
    def create(cls, userProfile: UserProfile, expire: datetime.datetime, dbSession: so.Session) -> "UserProfileSession":
        """
        Creates a new UserProfileSessions instance.

        :param userProfile: The user profile associated with the session.
        :param expire: The expiration datetime of the session.
        :param dbSession: The dbSession to make the query.

        :return: A new instance of UserProfileSessions with the provided profile and expiration.
        """
        try:
            logger.debug(f"Initializing session from user profile: {userProfile.facebookId=}")
            instance = cls(
                profile=userProfile,
                expire=expire,
                sessionToken=hashlib.md5(f"{userProfile.facebookId}{str(uuid.uuid4())}".encode()).hexdigest(),
            )
        except Exception as e:
            logger.error(e)
            raise Exception("Session Creation Failed")

        try:
            logger.debug(f"Writing session data for: {userProfile.facebookId=}, {instance.sessionToken[:5]=}")
            dbSession.add(instance)
            dbSession.commit()
            return instance
        except Exception as e:
            logger.error(f"Error creating session for user {userProfile.facebookId=}, {e}")
            raise Exception("Error creating user session")

    @classmethod
    def get(cls, sessionToken: str, currentTime: datetime.datetime, dbSession: so.Session) -> UserProfile | None:
        """
        Get profile from sessionToken with expire check

        :param sessionToken: The Sesion Token.
        :param currentTime: The current Time Stamp.
        :param dbSession: The dbSession to make the query.

        :return: The user profile associated with the given session token. or None      
        """
        try:
            logger.debug(f"getting profile for {sessionToken[:10]=}")
            queryResault = dbSession.query(cls).where(cls.sessionToken == sessionToken).first()
        except Exception as e:
            logger.error(e)
            raise Exception("Error querying db")

        if queryResault is None:
            logger.debug(f"session Token: {sessionToken[:10]=} - not found in db")
            return None

        try:
            logger.debug(f"session Token: {sessionToken[:10]=} - checking expirery")
            if currentTime >= pytz.UTC.localize(queryResault.expire):
                logger  .debug(f"session Token: {sessionToken[:10]=} - expired, delete in db")
                dbSession.delete(queryResault)
                dbSession.commit()
                return None
        except Exception as e:
            logger.error(e)
            raise Exception("Error removing expired token")

        return queryResault.profile

    @classmethod
    def clearProfile(cls, userProfile: UserProfile, dbSession: so.Session) -> None:
        """
        Delete all session for a user profile

        :param userProfile: The user profile associated with the session.
        :param dbSession: The dbSession to make the query.

        :return: None
        """
        try:
            logger.debug(f"Deleting userprofile session {userProfile.facebookId=}")
            dbSession.query(cls).where(cls.profile == userProfile).delete()
            dbSession.commit()
        except Exception as e:
            logger.error(e)
            raise Exception(f"Error removing token for profile {str(userProfile.facebookId)[:10]=}")
