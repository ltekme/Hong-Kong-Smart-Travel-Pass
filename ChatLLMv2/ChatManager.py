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
    pass


class MessageContext(TableBase):
    __tablename__ = "message_context"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    value: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chat_messages.id"))
    message: so.Mapped["ChatMessage"] = so.relationship(back_populates="contexts")

    # End of SqlAlchemyMapping
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    @property
    def asText(self) -> str:
        return f"{self.name}: {self.value}"


class MessageAttachment(TableBase):
    __tablename__ = "message_attachments"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    mime_type: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    blob_name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    base_data_path: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chat_messages.id"))
    message: so.Mapped["ChatMessage"] = so.relationship(back_populates="attachments")

    # End of SqlAlchemyMapping
    _base64Data: str = ""

    def __init__(self, dataUrl: str, base_data_path: str = "./data/msg_attachment"):
        logger.debug(f"Starting check for {dataUrl}")

        if not dataUrl.startswith("data"):
            raise ValueError("dataUrl must be javascrip data url")
        if not os.path.exists(base_data_path):
            os.makedirs(base_data_path)
        self.base_data_path = base_data_path

        logger.debug(f"Parcing {dataUrl[:30]=} to md5 for blobname")
        self.blob_name = hashlib.md5(dataUrl.encode()).hexdigest()
        # data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==
        mime_type = dataUrl.split(";")[0].split(":")[1]
        data = dataUrl.split(",")[1]

        if mime_type.split("/")[0] == "image" and mime_type.split("/")[0] != "gif":
            logger.debug(f"Starting Image convert to png")
            target_format = "png"
            processed_image = BytesIO()
            im = Image.open(BytesIO(base64.b64decode(data)))
            im.save(processed_image, target_format)
            data = base64.b64encode(processed_image.getvalue()).decode()
            mime_type = f"image/{target_format}"

        self.mime_type = mime_type
        self.base64Data = data

    @property
    def base64Data(self) -> str:
        logger.debug(f"fetching {self.blob_name} base64 data")
        if self._base64Data:
            logger.debug(f"found in cache returning")
            return self._base64Data
        fullDataPath = os.path.join(self.base_data_path, self.blob_name)
        logger.debug(f"getting data from {fullDataPath}")
        if not os.path.exists(fullDataPath):
            logger.warning(f"data not found at {fullDataPath} returning \"\"")
            return ""
        with open(fullDataPath, "rb") as f:
            return f.read().decode('ascii')

    @base64Data.setter
    def base64Data(self, value: str) -> None:
        self._base64Data = value
        fullDataPath = os.path.join(self.base_data_path, self.blob_name)
        logger.debug(f"storeing data to {fullDataPath}")
        with open(fullDataPath, 'wb') as f:
            f.write(self._base64Data.encode("ascii"))

    @property
    def asLcMessageDict(self) -> dict[str, str]:
        return {
            "type": "media",
            "data": self.base64Data,
            "mime_type": self.mime_type,
        }


class ChatMessage(TableBase):
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

    # End of SqlAlchemyMapping

    def __init__(self, role: t.Literal["user", "ai", "system"], text: str, attachments: t.List[MessageAttachment] = []):
        self.role = role
        self.text = text
        self.attachments = attachments

    lcMessageMapping: dict[str, t.Type[AIMessage | SystemMessage | HumanMessage]] = {
        "ai": AIMessage,
        "system": SystemMessage,
        "user": HumanMessage
    }

    @property
    def asLcMessageList(self) -> list[dict[str, str]]:
        return [{
            "type": "text",
            "text": f"{self.text}\n\nMessageContext\n<<EOF\n{'\n'.join(list(map(lambda c: c.asText, self.contexts)))}",
        }] + list(map(lambda x: x.asLcMessageDict, self.attachments))

    @property
    def asExportDict(self) -> dict[str, str | list[dict[str, str]]]:
        return {
            "role": self.role,
            "content": self.asLcMessageList
        }

    @property
    def asLcMessageObject(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
        return self.lcMessageMapping[self.role](content=self.asLcMessageList)  # type: ignore


class ChatRecord(TableBase):
    __tablename__ = "chats"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chatId: so.Mapped[str] = so.mapped_column(sa.String, default=str(uuid4()), nullable=False, unique=True)
    messages: so.Mapped[t.List["ChatMessage"]] = so.relationship(back_populates="chat")
    systemMessage: so.Mapped[str] = so.mapped_column(sa.String, default="", unique=False,)
    __allow_unmapped__ = True

    # End of SqlAlchemyMapping
    dbSession: so.Session

    def __init__(self, chatId: str = str(uuid4()), messages: list[ChatMessage] = [], systemMessage: str = ""):
        self.chatId = chatId
        self.messages = messages
        self.systemMessage = systemMessage

    @classmethod
    def init(cls, dbSession: so.Session, chatId: str = str(uuid4())) -> "ChatRecord":
        logger.info(f"Initializing {__name__} from chatId")
        instance = cls(chatId)
        existingChat = dbSession.query(cls).filter(cls.chatId == chatId).first()
        instance = existingChat if existingChat is not None else instance
        dbSession.add(instance)
        return instance

    def add_message(self, message: ChatMessage):
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
        return list(map(lambda msg: msg.asLcMessageObject, self.messages))
