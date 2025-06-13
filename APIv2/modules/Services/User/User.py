import hashlib
import random
import datetime
import typing as t

import sqlalchemy.orm as so

from fastapi import HTTPException

from .Role import RoleService
from .UserRole import UserRoleService
from ..Base import ServiceBase
from ..RandomPet import getRandomAnimal
from ...ApplicationModel import (
    User,
    UserSession,
    UserChatRecord,
)

from ....config import settings


class UserService(ServiceBase):
    def __init__(self, dbSession: so.Session, roleService: RoleService, userRoleService: UserRoleService) -> None:
        super().__init__(dbSession, serviceName="UserService")
        self.roleService = roleService
        self.userRoleService = userRoleService

    def createUser(self, username: str) -> User:
        """
        Create a user profile.
        :param username: The username of the user.
        :return: The user profile instance.
        """
        self.loggerDebug(f"Creating user with username: {username}")
        instance = User(username)
        self.dbSession.add(instance)
        return instance

    def createAnonymous(self, username: t.Optional[str] = None) -> User:
        """
        Create an anonymous user.
        :param username: The username of the user. If None, a random animal name will be used.

        :return: The user profile instance.
        """
        username = username if username else f"Anonymous {getRandomAnimal().capitalize()}"
        user = self.createUser(username)
        role = self.roleService.getOrCreateRole("Anonymous")
        self.userRoleService.associateUserWithRole(user, role)
        return user


class UserChatRecordService(ServiceBase):
    def __init__(self, dbSession: so.Session) -> None:
        super().__init__(dbSession, serviceName="UserChatRecordService")

    def getByChatId(self, chatId: str) -> t.Optional[UserChatRecord]:
        """
        Get a user chat record by chat ID.
        :param chatId: The chat ID to search for.
        :return: The user chat record instance or None if not found.
        """
        return self.dbSession.query(UserChatRecord).where(UserChatRecord.chatId == chatId).first()

    def associateChatIdWithUser(self, chatId: str, user: User) -> UserChatRecord:
        """
        Associate a chat ID with a user profile.
        :param chatId: The chat ID to associate.
        :param User: The user profile to associate with the chat ID.
        """
        record = UserChatRecord(chatId=chatId, user=user)
        self.dbSession.add(record)
        return record


class UserSessionService(ServiceBase):
    def __init__(self, dbSession: so.Session) -> None:
        super().__init__(dbSession, serviceName="UserSessionService")

    def creaeteExpirDatetime(self) -> datetime.datetime:
        """
        Create an expiration datetime for a session.
        :return: The expiration datetime.
        """
        return datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=settings.userSessionExpireInSeconds)

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

    def createForUser(self, user: User, expire: t.Optional[datetime.datetime] = None) -> UserSession:
        """
        Create a session for a user profile.
        :param User: The user profile to create a session for.
        :param expire: The expiration datetime for the session.
        :return: The created session.
        """
        expire = expire if expire else self.creaeteExpirDatetime()
        semiEncodedString = f"{user.id}{str(random.random())}{datetime.datetime.now(datetime.UTC)}"
        instance = UserSession(
            user=user,
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

    def clearExpiredUserSession(self, User: User) -> None:
        """
        Clear expired user sessions.
        :param User: The user profile to clear sessions for.
        """
        self.dbSession.query(UserSession).where(
            UserSession.user == User,
            UserSession.expire < datetime.datetime.now(datetime.UTC)
        ).delete()

    def validateSessionToken(self, sessionToken: t.Optional[str], bypassExpire: bool = False, updateExperation: bool = True) -> UserSession:
        """
        Validate the session token. 
        Used in API endpoints to ensure the session is valid before proceeding with the request.
        Raises an HTTPException if the session token is invalid or expired.
        Not to be used in the service layer, but rather in the API layer.

        When `updateExperation` is True, the expiration date of the session token will be updated.

        :param sessionToken: The session token to validate.
        :param userSessionService: The user session service to use.
        :param updateExperation: Whether to update the expiration date of the session token.

        :raises HTTPException: If the session token is invalid or expired.
        :return: True if the session token is valid.
        """
        if sessionToken is None or not sessionToken.strip():
            raise HTTPException(
                status_code=400,
                detail="No Session Found"
            )
        if updateExperation:
            session = self.updateExpiration(sessionToken=sessionToken, overide=bypassExpire)
        else:
            session = self.getSessionFromSessionToken(
                sessionToken=sessionToken,
                bypassExpire=bypassExpire
            )
        if session is None:
            raise HTTPException(
                status_code=400,
                detail="Session Expired or invalid"
            )
        return session
