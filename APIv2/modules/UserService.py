import uuid
import random
import hashlib
import datetime
import typing as t
import sqlalchemy.orm as so

from .ApplicationModel import (
    SocialsProfileProvider,
    UserSocialProfile,
    UserProfile,
    UserChatRecord,
    UserSession
)
from . import FacebookClient
from ..config import logger, animals


class FacebookUserIdentifyExeception(Exception):
    pass


def getRandomAnimal():
    return random.choice(animals)


def getOrCreateSocialsProfileProvider(name: str, dbSession: so.Session) -> SocialsProfileProvider:
    """
    Create or get a socials profile provider

    :param name: The name of the provider.
    :param dbSession: The database session to use.
    """
    provider = dbSession.query(SocialsProfileProvider).where(SocialsProfileProvider.name == name).first()
    if provider is not None:
        return provider
    provider = SocialsProfileProvider(name)
    dbSession.add(provider)
    dbSession.commit()
    return provider


def queryUserSocialProfile(provider: SocialsProfileProvider, socialId: str, dbSession: so.Session) -> t.Optional[UserSocialProfile]:
    """
    Query the database for a user profile from social profile

    :param provider (SocialsProfileProvider): The social provider .
    :param socialId: The Id of the social profile.
    :param dbSession: The database session to use.
    """
    record = dbSession.query(
        UserSocialProfile
    ).where(
        UserSocialProfile.provider == provider and UserSocialProfile.socialId == socialId
    ).first()
    if record is not None:
        return record


def createAnonymousUser(dbSession: so.Session) -> UserProfile:
    """
    Create an anonymous user

    :param dbSession: The database session to use.
    """
    try:
        instance = UserProfile(f"Anonymous {getRandomAnimal().capitalize()}")
        instance.public = True
        dbSession.add(instance)
        dbSession.commit()
        return instance
    except Exception as e:
        logger.error(e)
        raise Exception(f"Error creating Anonymous User")


def getUserProfileFromFacebookAccessToken(accessToken: str, dbSession: so.Session) -> UserProfile:
    """
    Get UserProfile instance from facebook access token.

    :param accessToken: The access token of a given facebook user.
    :param dbSession: The database session to use.

    :return: A new instance of UserProfile with Id and username populated.
    """
    try:
        facebookProfile = FacebookClient.getUsernameAndId(accessToken=accessToken)
    except Exception as e:
        logger.error(f"Error performing user identification, {e}")
        raise FacebookUserIdentifyExeception("Error performing facebook user identification")

    provider = getOrCreateSocialsProfileProvider('facebook', dbSession)
    userProfile = queryUserSocialProfile(
        socialId=str(facebookProfile.facebookId),
        provider=provider,
        dbSession=dbSession
    )
    if userProfile is not None:
        return userProfile.profile
    instance = UserProfile(facebookProfile.username)
    dbSession.add(instance)
    dbSession.commit()
    return instance


def getUserProfileFromSessionToken(sessionToken: str, dbSession: so.Session, bypassExpire: bool = False) -> t.Optional[UserProfile]:
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

    if record.expire < datetime.datetime.now(datetime.UTC) and not bypassExpire:
        logger.info(f"session Token: {sessionToken[:10]=} has been expired at {record.expire}")
        dbSession.delete(record)
        dbSession.commit()
        return None

    return record.profile


def getUserProfileChatRecordFromChatId(chatId: str, dbSession: so.Session) -> t.Optional[UserChatRecord]:
    """
    Get associated User Profile of a chatId

    :param chatId: The chatId.
    :param dbSession: The dbSession to make the query.

    :return: A new instance of UserProfile or None.
    """
    record = dbSession.query(UserChatRecord).where(
        UserChatRecord.chatId == chatId
    ).first()
    if record is not None:
        return record


def associateChatIdWithUserProfile(chatId: str, userProfile: UserProfile, dbSession: so.Session) -> UserChatRecord:
    """
    Add chat user pair record

    :param chatId: The chatId.
    :param userProfile: The User Profile.
    :param dbSession: The dbSession to make the query.

    :return: UserChatRecord
    """
    record = UserChatRecord(chatId=chatId, userProfile=userProfile)
    dbSession.add(record)
    dbSession.commit()
    return record


def createUserSession(userProfile: UserProfile, expire: datetime.datetime, dbSession: so.Session) -> UserSession:
    """
    Creates a new UserSessions instance.

    :param userProfile: The user profile associated with the session.
    :param expire: The expiration datetime of the session.
    :param dbSession: The dbSession to make the query.

    :return: A new instance of UserSessions with the provided profile and expiration.
    """
    logger.info(f"Initializing session from user profile: {userProfile.id=}")
    instance = UserSession(
        profile=userProfile,
        expire=expire,
        sessionToken=hashlib.md5(f"{userProfile.id}{str(uuid.uuid4())}".encode()).hexdigest(),
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
