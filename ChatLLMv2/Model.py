import typing as t
import sqlalchemy as sa
import sqlalchemy.orm as so


class Base(so.DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chats"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    # chat messages relations
    messages: so.Mapped[t.List["Message"]] = so.relationship(back_populates="chat")


class Message(Base):
    __tablename__ = "messages"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    role: so.Mapped[t.Literal["user", "ai", "system"]] = so.mapped_column(sa.String, nullable=False)

    # message content
    content: so.Mapped["MessageContent"] = so.relationship(back_populates="message")

    # message chat relation
    chat_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"chats.id"))
    chat: so.Mapped["Chat"] = so.relationship(back_populates="messages")

    # constraints
    __table_args__ = (
        sa.CheckConstraint("role IN ('user', 'ai', 'system')", name="check_role"),
    )


class MessageContent(Base):
    __tablename__ = "message_contents"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    text: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    # content media
    attachment: so.Mapped[t.List["ContentAttachment"]] = so.relationship(back_populates="message_content")

    # message content relations
    message_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("messages.id"))
    message: so.Mapped["Message"] = so.relationship(back_populates="content")


class ContentAttachment(Base):
    __tablename__ = "content_medias"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    attachment_type: so.Mapped[t.Literal["document", "media"]] = so.mapped_column(sa.String, nullable=False)
    blob_name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    # content media relations
    message_content_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(f"message_contents.id"))
    message_content: so.Mapped["MessageContent"] = so.relationship(back_populates="attachment")

    # constraints
    __table_args__ = (
        sa.CheckConstraint("attachment_type IN ('document', 'media')", name="check_attachment_type"),
    )
