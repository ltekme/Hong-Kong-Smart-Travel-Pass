# Importing to extend exisiting table
# No Cross Refernece between tables should be defined
# I don't think this is recommended but it works
# The Mappings here should never have any effect on data in from ChatLLMv2
# All mappings here is seperate from ChatLLMv2 as ChatLLMv2 is a seperate core component that can work on it own.
import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import TableBase


class UserProfile(TableBase):
    __tablename__ = "user_profile"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String)
    facebookId: so.Mapped[int] = so.mapped_column(sa.String, nullable=False, index=True)
    chatRecordIds: so.Mapped[t.List["UserProifileChatRecords"]] = so.relationship(back_populates="_profile")

    @classmethod
    def fromFacebookAccessKey(cls, accessKeyId: str):
        """
        Initialize UserProfile instance from facebook access key.

        :param accessKeyId: The access key of a given facebook user.
        """
        instance = cls()
        instance.facebookId


class UserProifileChatRecords(TableBase):
    __tablename__ = "user_proifile_chat_records"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    profile: so.Mapped["UserProfile"] = so.relationship(back_populates="chatRecords")
    chatId: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True, index=True)

    pass
