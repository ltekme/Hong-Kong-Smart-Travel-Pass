import sqlalchemy.orm as so

from .socials import *

from ..ApplicationModel import (
    UserProfile
)
from .. import FacebookClient
from ...config import logger

from .user import getOrCreateUserProfileType


class FacebookUserIdentifyExeception(Exception):
    pass


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
    userType = getOrCreateUserProfileType("Facebook", dbSession)
    userProfile = queryUserSocialProfile(
        socialId=str(facebookProfile.facebookId),
        provider=provider,
        dbSession=dbSession
    )
    if userProfile is not None:
        return userProfile.profile
    instance = UserProfile(facebookProfile.username, userType)
    dbSession.add(instance)
    dbSession.commit()
    return instance
