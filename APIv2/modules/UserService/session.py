import pytz
import random
import hashlib
import datetime
import typing as t
import sqlalchemy.orm as so

from ..ApplicationModel import (
    UserProfile,
    UserSession
)
from ...config import logger, settings


def createSessionTokenExpireDatetime():
    """
    Create a session token expiration datetime.
    :return: A datetime object representing the expiration date.
    """
    currentDatetime = datetime.datetime.now(datetime.UTC)
    timeDelta = datetime.timedelta(seconds=settings.userSessionExpireInSeconds)
    sessionExpireDatetime = currentDatetime + timeDelta
    return sessionExpireDatetime


def sessionDatetimeExpired(
    sessionDatetime: datetime.datetime,
) -> bool:
    """
    Check if the session token is expired.

    :param sessionDatetime: The session token expire datetime.

    :return: True if the session token is expired, False otherwise.
    """
    return sessionDatetime.replace(tzinfo=pytz.UTC) < datetime.datetime.now(datetime.UTC)


def createUserSession(
    userProfile: UserProfile,
    dbSession: so.Session,
    expire: t.Optional[datetime.datetime] = None
) -> UserSession:
    """
    Creates a new UserSessions instance.

    :param userProfile: The user profile associated with the session.
    :param expire: The expiration datetime of the session.
    :param dbSession: The dbSession to make the query.

    :return: A new instance of UserSessions with the provided profile and expiration.
    """
    logger.info(f"Initializing session from user profile: {userProfile.id=}")
    if not expire:
        expire = createSessionTokenExpireDatetime()
    encoString = f"{userProfile.id}{str(random.random())}{datetime.datetime.now(datetime.UTC)}"
    instance = UserSession(
        profile=userProfile,
        expire=expire,
        sessionToken=hashlib.md5(encoString.encode()).hexdigest(),
    )
    dbSession.add(instance)
    dbSession.commit()
    return instance


def clearExpiredUserSession(userProfile: UserProfile, dbSession: so.Session) -> None:
    """
    Delete all session for a user profile

    :param userProfile: The user profile associated with the session.
    :param dbSession: The dbSession to make the query.

    :return: None
    """
    logger.debug(f"Deleting expired userprofile session {userProfile.id=}")
    dbSession.query(UserSession).where(
        UserSession.profile == userProfile and UserSession.expire < datetime.datetime.now(datetime.UTC)
    ).delete()
    dbSession.commit()


def updateSessionTokenExpiration(
    sessionToken: str,
    dbSession: so.Session,
    expire: t.Optional[datetime.datetime] = None,
    overide: bool = False
) -> UserSession | None:
    """
    Update the expiration date of a session token.

    :param sessionToken: The session token to update.
    :param expire: The new expiration date.
    :param dbSession: The database session to use.
    :return: The updated expiration date.
    """
    if not expire:
        expire = createSessionTokenExpireDatetime()
    session = dbSession.query(UserSession).where(
        UserSession.sessionToken == sessionToken
    ).first()
    if session is None:
        logger.warning(f"session Token: {sessionToken[:10]=} - not found in db")
        return None
    if sessionDatetimeExpired(session.expire) and not overide:
        logger.info(f"session Token: {sessionToken[:10]=} has been expired at {session.expire}")
        dbSession.delete(session.expire)
        dbSession.commit()
        return None
    logger.info(f"Updating session Token: {sessionToken[:10]=} - {session.expire=} to {expire}")
    session.expire = expire
    dbSession.commit()
    return session


def getUserProfileFromSessionToken(
    sessionToken: str,
    dbSession: so.Session,
    bypassExpire: bool = False
) -> t.Optional[UserProfile]:
    """
    Get associated User Profile of a chatId

    :param sessionToken: The session token.
    :param dbSession: The dbSession to make the query.
    :param bypassExpire: Skip session expire check.

    :return: A new instance of UserProfile or None.
    """
    record = dbSession.query(UserSession).where(
        UserSession.sessionToken == sessionToken
    ).first()

    if record is None:
        logger.info(f"session Token: {sessionToken[:10]=} - not found in db")
        return None

    if sessionDatetimeExpired(record.expire) and not bypassExpire:
        logger.info(f"session Token: {sessionToken[:10]=} has been expired at {record.expire}")
        dbSession.delete(record)
        dbSession.commit()
        return None

    return record.profile
