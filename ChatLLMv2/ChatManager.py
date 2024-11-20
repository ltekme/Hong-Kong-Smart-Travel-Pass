import os
import base64
import logging
import hashlib
import typing as t
from PIL import Image
from io import BytesIO
from uuid import uuid4
import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy.sql as sl
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


logger = logging.getLogger(__name__)


class TableBase(so.DeclarativeBase):
    """Base class for SQLAlchemy table definitions."""
    pass


class MessageContext(TableBase):
    """Represents the context of a message in the chat."""
    __tablename__ = "message_context"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    value: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chat_messages.id"))
    message: so.Mapped["ChatMessage"] = so.relationship(back_populates="contexts")

    def __init__(self, name: str, value: str) -> None:
        """
        Initialize a MessageContext instance.

        :param name: The name of the context.
        :param value: The value of the context.
        """
        self.name = name
        self.value = value

    @property
    def asText(self) -> str:
        """
        Convert the context to a text representation.

        :return: A string representation of the context.
        """
        return f"{self.name}: {self.value};"


class MessageAttachment(TableBase):
    """Represents an attachment in a chat message."""
    __tablename__ = "message_attachments"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    mimeType: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    blobName: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    baseDataPath: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chat_messages.id"))
    message: so.Mapped["ChatMessage"] = so.relationship(back_populates="attachments")

    _base64Data: str = ""

    def __init__(self, dataUrl: str, baseDataPath: str = "./data/messageAttachment") -> None:
        """
        Initialize a MessageAttachment instance.

        :param dataUrl: The javascript data URL of the attachment.
        :param baseDataPath: The base path to store the attachment data.
        """
        logger.debug(f"Starting check for {dataUrl}")

        if not dataUrl.startswith("data"):
            raise ValueError("dataUrl must be a javascript data URL")
        if not os.path.exists(baseDataPath):
            os.makedirs(baseDataPath)
        self.baseDataPath = baseDataPath

        logger.debug(f"Parsing {dataUrl[:30]=} to md5 for blobname")
        self.blobName = hashlib.md5(dataUrl.encode()).hexdigest()
        mimeType = dataUrl.split(";")[0].split(":")[1]
        data = dataUrl.split(",")[1]

        if mimeType.split("/")[0] == "image" and mimeType.split("/")[1] != "gif":
            logger.debug(f"Starting Image convert to png")
            targetFormat = "png"
            processedImage = BytesIO()
            try:
                im = Image.open(BytesIO(base64.b64decode(data)))
                im.verify()
                im.save(processedImage, targetFormat)
                data = base64.b64encode(processedImage.getvalue()).decode()
                mimeType = f"image/{targetFormat}"
            except Exception as e:
                logger.error(f"Invalid image data: {e}")
                raise ValueError("Invalid image data")

        if mimeType == "image/gif":
            logger.debug(f"Starting Image verify for gif")
            try:
                im = Image.open(BytesIO(base64.b64decode(data)))
                im.verify()
            except Exception as e:
                logger.error(f"Invalid gif data: {e}")
                raise ValueError("Invalid gif data")

        self.mimeType = mimeType
        self.base64Data = data

    @property
    def base64Data(self) -> str:
        """
        Get the base64 encoded data of the attachment.

        :return: The base64 encoded data.
        """
        logger.debug(f"fetching {self.blobName} base64 data")
        if self._base64Data:
            logger.debug(f"found in cache returning")
            return self._base64Data
        fullDataPath = os.path.join(self.baseDataPath, self.blobName)
        logger.debug(f"getting data from {fullDataPath}")
        if not os.path.exists(fullDataPath):
            logger.warning(f"data not found at {fullDataPath} returning \"\"")
            return ""
        with open(fullDataPath, "rb") as f:
            return f.read().decode('ascii')

    @base64Data.setter
    def base64Data(self, value: str) -> None:
        """
        Set the base64 encoded data of the attachment.

        :param value: The base64 encoded data.
        """
        self._base64Data = value
        fullDataPath = os.path.join(self.baseDataPath, self.blobName)
        logger.debug(f"storeing data to {fullDataPath}")
        with open(fullDataPath, 'wb') as f:
            f.write(self._base64Data.encode("ascii"))

    @property
    def asLcMessageDict(self) -> dict[str, str]:
        """
        Convert the attachment to a dictionary representation.

        :return: A dictionary representation of the attachment.
        """
        return {
            "type": "media",
            "data": self.base64Data,
            "mime_type": self.mimeType,
        }


class ChatMessage(TableBase):
    """Represents a chat message."""
    __tablename__ = "chat_messages"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    role: so.Mapped[t.Literal["user", "ai", "system"]] = so.mapped_column(sa.String, nullable=False)
    text: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    dateTime: so.Mapped[sa.DateTime] = so.mapped_column(sa.DateTime(timezone=True), default=sl.func.now())
    contexts: so.Mapped[t.List["MessageContext"]] = so.relationship(back_populates="message")
    attachments: so.Mapped[t.List["MessageAttachment"]] = so.relationship(back_populates="message")
    chat_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chats.id"))
    chat: so.Mapped["ChatRecord"] = so.relationship(back_populates="messages")
    __table_args__ = (
        sa.CheckConstraint("role IN ('user', 'ai', 'system')", name="check_role"),
    )

    def __init__(self, role: t.Literal["user", "ai", "system"],
                 text: str, attachments: t.List[MessageAttachment] = [],
                 contexts: t.List[MessageContext] = []) -> None:
        """
        Initialize a ChatMessage instance.

        :param role: The role of the message sender.
        :param text: The text content of the message.
        :param attachments: A list of attachments in the message.
        :param contexts: A list of contexts for the message.
        """
        self.role = role
        self.text = text
        self.attachments = attachments
        self.contexts = contexts

    @property
    def lcMessageMapping(self) -> dict[str, t.Type[AIMessage | SystemMessage | HumanMessage]]:
        """
        Get the mapping of roles to message types.

        :return: A dictionary mapping roles to message types.
        """
        return {
            "ai": AIMessage,
            "system": SystemMessage,
            "user": HumanMessage
        }

    @property
    def asLcMessageList(self) -> list[dict[str, str]]:
        """
        Convert the message to a list of dictionary representations.

        :return: A list of dictionary representations of the message.
        """
        contextText = f"\n\nMessageContext << EOF\n{'\n'.join(list(map(lambda c: c.asText, self.contexts)))}\nEOF"
        return [{
            "type": "text",
            "text": self.text + (contextText if len(self.contexts) > 0 else ""),
        }] + list(map(lambda x: x.asLcMessageDict, self.attachments))

    @property
    def asLcMessageObject(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
        """
        Convert the message to a LangChain message object.

        :return: A LangChain message object.
        """
        return self.lcMessageMapping[self.role](content=self.asLcMessageList)  # type: ignore


class ChatRecord(TableBase):
    """Represents a chat record."""
    __tablename__ = "chats"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chatId: so.Mapped[str] = so.mapped_column(sa.String, default=str(uuid4()), nullable=False, unique=True)
    messages: so.Mapped[t.List["ChatMessage"]] = so.relationship(back_populates="chat")
    systemMessage: so.Mapped[str] = so.mapped_column(sa.String, default="", unique=False,)
    __allow_unmapped__ = True

    def __init__(self, chatId: str = str(uuid4()), messages: list[ChatMessage] = [], systemMessage: str = ""):
        """
        Initialize a ChatRecord instance.

        :param chatId: The unique identifier for the chat.
        :param messages: A list of messages in the chat.
        :param systemMessage: The system message for the chat.
        """
        self.chatId = chatId
        self.messages = messages
        self.systemMessage = systemMessage

    @classmethod
    def init(cls, dbSession: so.Session, chatId: str = str(uuid4())) -> "ChatRecord":
        """
        Initialize a ChatRecord instance from the database.

        :param dbSession: The database session.
        :param chatId: The unique identifier for the chat.
        :return: An instance of ChatRecord.
        """
        logger.info(f"Initializing {__name__} from chatId")
        instance = cls(chatId)
        existingChat = dbSession.query(cls).filter(cls.chatId == chatId).first()
        instance = existingChat if existingChat is not None else instance
        dbSession.add(instance)
        return instance

    def add_message(self, message: ChatMessage):
        """
        Add a message to the chat.

        :param message: The message to add.
        :raises ValueError: If the message role is invalid or consecutive messages have the same role.
        """
        logger.debug(f"Adding message to chat {self.chatId}, {message.role=}:{message.text[:10]=}")
        if message.role not in ["user", "system", "ai"]:
            raise ValueError(f'message role must be one of ["user", "system", "ai"]')
        if len(self.messages) == 0 and message.role == "ai":
            raise ValueError("Cannot append message role=AI on the first message")
        if len(self.messages) > 0 and self.messages[-1].role == "ai" and message.role == "ai":
            raise ValueError("Cannot have consective AI message")
        if len(self.messages) > 0 and self.messages[-1].role == "user" and message.role == "user":
            raise ValueError("Cannot have consective USER message")
        logger.debug(f"Checks passed added message to chat {self.chatId}, {message.role=}:{message.text[:10]=}")
        self.messages.append(message)

    @property
    def asLcMessages(self) -> list[t.Union[AIMessage, SystemMessage, HumanMessage]]:
        """
        Convert the chat record to a list of LangChain message objects.

        :return: A list of LangChain message objects.
        """
        return list(map(lambda msg: msg.asLcMessageObject, self.messages))
