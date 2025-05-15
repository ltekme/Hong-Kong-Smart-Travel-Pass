import hashlib
import random
import datetime
import typing as t
import sqlalchemy.orm as so

from .base import ServiceBase
from .RandomPet import getRandomAnimal

from ..ApplicationModel import UserType, UserProfile, UserChatRecord, UserSession


class UserTypeService(ServiceBase):

    def getByName(self, name: str) -> t.Optional[UserType]:
        """
        Get a user type by name.
        :param name: The name of the user type.
        :return: The user type instance.
        """
        return self.dbSession.query(UserType).where(UserType.name == name).first()

    def createByName(self, name: str) -> UserType:
        """
        Create a user type by name.
        :param name: The name of the user type.
        :return: The user type instance.
        """
        instance = UserType(name)
        self.dbSession.add(instance)
        return instance

    def getOrCreateByName(self, name: str) -> UserType:
        """
        Get or create a user type by name.
        :param name: The name of the user type.
        :return: The user type instance.
        """
        instance = self.getByName(name)
        if instance is not None:
            return instance
        return self.createByName(name)


class UserService(ServiceBase):

    def __init__(self, dbSession: so.Session, userTypeService: UserTypeService) -> None:
        super().__init__(dbSession)
        self.userTypeService = userTypeService

    def createUserProfile(self, username: str, userType: UserType) -> UserProfile:
        """
        Create a user profile.
        :param username: The username of the user.
        :param userType: The type of the user.
        :return: The user profile instance.
        """
        instance = UserProfile(username, type=userType)
        self.dbSession.add(instance)
        return instance

    def createAnonymous(self, username: t.Optional[str] = None, userType: t.Optional[UserType] = None) -> UserProfile:
        """
        Create an anonymous user.
        :return: The user profile instance.
        """
        userType = userType if userType else self.userTypeService.getOrCreateByName("Anonymous")
        username = username if username else f"Anonymous {getRandomAnimal().capitalize()}"
        user = self.createUserProfile(username, userType)
        self.dbSession.add(user)
        return user


class UserChatRecordService(ServiceBase):

    def getByChatId(self, chatId: str) -> t.Optional[UserChatRecord]:
        """
        Get a user chat record by chat ID.
        :param chatId: The chat ID to search for.
        :return: The user chat record instance or None if not found.
        """
        return self.dbSession.query(UserChatRecord).where(UserChatRecord.chatId == chatId).first()

    def associateChatIdWithUserProfile(self, chatId: str, userProfile: UserProfile) -> UserChatRecord:
        """
        Associate a chat ID with a user profile.
        :param chatId: The chat ID to associate.
        :param userProfile: The user profile to associate with the chat ID.
        """
        record = UserChatRecord(chatId=chatId, userProfile=userProfile)
        self.dbSession.add(record)
        return record


class UserSessionService(ServiceBase):

    def creaeteExpirDatetime(self) -> datetime.datetime:
        """
        Create an expiration datetime for a session.
        :return: The expiration datetime.
        """
        return datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    def expired(self, session: UserSession) -> bool:
        """
        Check if a session is expired.
        :param session: The session to check.
        :return: True if the session is expired, False otherwise.
        """
        return datetime.datetime.now(datetime.UTC) > session.expire.replace(tzinfo=datetime.UTC)

    def getSessionFromSessionToken(self, sessionToken: str, bypassExpire: bool = False) -> t.Optional[UserSession]:
        """
        Get a session from a session token.
        :param sessionToken: The session token to get.
        :param bypassExpire: Whether to bypass the expiration check.
        :return: The session instance or None if not found.
        """
        record = self.dbSession.query(UserSession).where(UserSession.sessionToken == sessionToken).first()
        if record is None:
            return None
        if self.expired(record) and not bypassExpire:
            self.dbSession.delete(record)
            return None
        return record

    def createForUserProfile(self, userProfile: UserProfile, expire: t.Optional[datetime.datetime] = None) -> UserSession:
        """
        Create a session for a user profile.
        :param userProfile: The user profile to create a session for.
        :param expire: The expiration datetime for the session.
        :return: The created session.
        """
        expire = expire if expire else self.creaeteExpirDatetime()
        semiEncodedString = f"{userProfile.id}{str(random.random())}{datetime.datetime.now(datetime.UTC)}"
        instance = UserSession(
            profile=userProfile,
            expire=expire,
            sessionToken=hashlib.md5(semiEncodedString.encode()).hexdigest(),
        )
        self.dbSession.add(instance)
        return instance

    def updateExpiration(self, sessionToken: str, expire: t.Optional[datetime.datetime] = None, overide: bool = False) -> t.Optional[UserSession]:
        """
        Update the expiration date of a session token.
        :param sessionToken: The session token to update.
        :param expire: The new expiration date.
        :param overide: Whether to override the expiration date if it is already expired.
        :return: The updated session or None if not found.
        """
        expire = expire if expire else self.creaeteExpirDatetime()
        session = self.getSessionFromSessionToken(sessionToken, bypassExpire=overide)
        if session is None:
            return None
        session.expire = expire
        return session

    def clearExpiredUserSession(self, userProfile: UserProfile) -> None:
        """
        Clear expired user sessions.
        :param userProfile: The user profile to clear sessions for.
        """
        self.dbSession.query(UserSession).where(
            UserSession.profile == userProfile,
            UserSession.expire < datetime.datetime.now(datetime.UTC)
        ).delete()
