import typing as t
import sqlalchemy.orm as so

from ..ApplicationModel import (
    UserProfile,
    UserChatRecord,
    UserType,

)
from .randomPet import getRandomAnimal
from ...config import logger


def getOrCreateUserProfileType(
    profileType: str,
    dbSession: so.Session,
) -> UserType:
    """
    Get or create a user profile type

    :param profileType: The profile type to get or create.
    :param dbSession: The database session to use.

    :return: A new instance of UserType .
    """
    instance = dbSession.query(UserType).where(
        UserType.name == profileType
    ).first()
    if instance is None:
        instance = UserType(profileType)
        dbSession.add(instance)
        dbSession.commit()
        return instance
    return instance


def createAnonymousUser(dbSession: so.Session) -> UserProfile:
    """
    Create an anonymous user

    :param dbSession: The database session to use.
    """
    try:
        userType = getOrCreateUserProfileType("Anonymous", dbSession)
        instance = UserProfile(f"Anonymous {getRandomAnimal().capitalize()}", type=userType)
        instance.type = userType
        dbSession.add(instance)
        dbSession.commit()
        return instance
    except Exception as e:
        logger.error(e)
        raise Exception(f"Error creating Anonymous User")


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
