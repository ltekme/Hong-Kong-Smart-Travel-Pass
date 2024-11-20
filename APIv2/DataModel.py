import typing as t
from pydantic import BaseModel


class MessageRequest(BaseModel):
    class MessageContext(BaseModel):
        message: str
        media: t.Optional[list[str]] = None

    chatId: str
    content: MessageContext
    context: t.Optional[dict[str, str]] = None
