import typing as t
import sqlalchemy.orm as so

from ..ApplicationModel import (
    SocialsProfileProvider,
    UserSocialProfile,
)


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
