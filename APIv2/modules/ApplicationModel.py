# Importing to extend exisiting table
# No Cross Refernece between tables should be defined
# I don't think this is recommended but it works
# The Mappings here should never have any effect on data in from ChatLLMv2
# All mappings here is seperate from ChatLLMv2 as ChatLLMv2 is a seperate core component that can work on it own.
# PS: There is virtually zero typing on facebook Graph API, might as well write raw requests
import logging
import facebook  # type: ignore
import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import TableBase

logger = logging.getLogger(__name__)


class UserProfile(TableBase):
    """Represents a user profile."""
    __tablename__ = "user_profile"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, index=True)
    facebookId: so.Mapped[int] = so.mapped_column(sa.String, nullable=False, index=True)
    chatRecordIds: so.Mapped[t.List["UserProifileChatRecords"]] = so.relationship(back_populates="profile")

    def __init__(self, username: str, facebookId: int):
        self.username = username
        self.facebookId = facebookId

    @classmethod
    def fromFacebookAccessToken(cls, accessToken: str) -> "UserProfile":
        """
        Initialize UserProfile instance from facebook access token.
        This is a basic im

        :param accessToken: The access token of a given facebook user.
        """
        logger.debug(f"Initializing user instance from facebook access key")
        graphApi = facebook.GraphAPI(access_token=accessToken, version="2.12")

        try:
            logger.debug(f"performing lookup for facebook user")
            facebookProfile = graphApi.get_object(id="me", fields="id,name")  # type: ignore
            instance = cls(
                username=facebookProfile["name"], # type: ignore
                facebookId=facebookProfile["id"], # type: ignore
            )
        except Exception as e:
            logger.error(f"Error performing user lookup, {e}")
            raise Exception("Error performing user lookup")

        logger.debug(f"Profile loaded: {instance.facebookId} ({instance.username})")
        return instance


class UserProifileChatRecords(TableBase):
    """Represents a semi key-value pair of user profile and chat records."""
    __tablename__ = "user_proifile_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"user_profile.id"))
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="chatRecordIds")
    chatId: so.Mapped[str] = so.mapped_column(sa.ForeignKey(f"chats.chatId"), nullable=True)
