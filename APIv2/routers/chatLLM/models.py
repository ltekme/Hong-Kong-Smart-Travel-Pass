# import datetime
import typing as t
from pydantic import BaseModel, Field


class chatLLMDataModel:

    class Request(BaseModel):
        class MessageContent(BaseModel):
            message: str = Field(
                description="The message that get sent to LLM"
            )
            media: t.Optional[list[str]] = Field(
                description="List of attachments along side of user text",
                default=None
            )

        chatId: str = Field(
            description="The chat ID, should be uuid string",
        )
        content: MessageContent = Field(
            description="content to be sent to LLM",
        )
        context: t.Optional[dict[str, str]] = Field(
            description="Context of this request, will be sent to LLM",
            default=None
        )
        location: t.Optional[str] = Field(
            description="Location string of this request, will be sent to LLM",
            default="Not Avalable"
        )
        disableTTS: t.Optional[bool] = Field(
            description="controls weather to include TTS audio data in the response",
            default=None
        )

    class Response(BaseModel):
        message: str = Field(
            description="LLM Response Message",
        )
        chatId: str = Field(
            description="The Chat id of the chat this message belong to",
        )
        ttsAudio: str = Field(
            description="TTS Audio data in base64",
        )

class ChatRecallModel:

    class ResponseMessage(BaseModel):
        role: t.Literal["user", "ai", "system"]
        message: str = Field(
            description="LLM Response Message",
        )
        dateTime: str = Field(
            description="The time of the message sent"
        )

    class Response(BaseModel):
        chatId: str = Field(
            description="The chat ID, should be uuid string",
        )
        messages: list["ChatRecallModel.ResponseMessage"] = Field(
            description="List of Messages",
        )
