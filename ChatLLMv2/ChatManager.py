import logging
import typing as t
from uuid import uuid4
import sqlalchemy as sa
import sqlalchemy.orm as so

logger = logging.getLogger(__name__)


class TableBase(so.DeclarativeBase):
    pass


class MessageAttachment(TableBase):
    __tablename__ = "message_attachments"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    type: so.Mapped[t.Literal["document", "media"]] = so.mapped_column(sa.String, nullable=False)
    blob_name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    # content attachment relations
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chat_messages.id"))
    message: so.Mapped["ChatMessage"] = so.relationship(back_populates="attachments")

    # constraints
    __table_args__ = (
        sa.CheckConstraint("type IN ('document', 'media')", name="check_attachment_type"),
    )

    def __init__(self, type: t.Literal["document", "media"], blob_name: str):
        self.type = type
        self.blob_name = blob_name


class ChatMessage(TableBase):
    __tablename__ = "chat_messages"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    role: so.Mapped[t.Literal["user", "ai", "system"]] = so.mapped_column(sa.String, nullable=False)
    text: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    # chat attachments
    attachments: so.Mapped[t.List["MessageAttachment"]] = so.relationship(back_populates="message")

    # message chat relation
    chat_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chats.id"))
    chat: so.Mapped["ChatRecord"] = so.relationship(back_populates="messages")

    # constraints
    __table_args__ = (
        sa.CheckConstraint("role IN ('user', 'ai', 'system')", name="check_role"),
    )

    def __init__(self, role: t.Literal["user", "ai", "system"], text: str, attachments: t.List[MessageAttachment] = []):
        self.role = role
        self.text = text
        self.attachments = attachments


class ChatRecord(TableBase):
    __tablename__ = "chats"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    chatId: so.Mapped[str] = so.mapped_column(nullable=False, default=str(uuid4()), unique=True)

    # chat messages relations
    messages: so.Mapped[t.List["ChatMessage"]] = so.relationship(back_populates="chat")

    def __init__(self, chatId: str = str(uuid4())):
        self.chatId = chatId

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
