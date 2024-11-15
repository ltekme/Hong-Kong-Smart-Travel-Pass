import typing as t
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class MessageContentMedia:
    def __init__(self, data: str, mime_type: str) -> None:
        self._data = data
        self._mime_type = mime_type

    @property
    def uri(self) -> str:
        return f"data:{self._mime_type};base64,{self._data}"

    @property
    def as_lcMessageDict(self) -> dict[str, t.Any]:
        return {
            # "type": "image_url",
            # "image_url": {"url": self.uri}
            "type": "media",
            "data": self._data,
            "mime_type": self._mime_type,
        }

    @classmethod
    def from_uri(cls, uri: str) -> "MessageContentMedia":
        if not uri.startswith("data"):
            raise ValueError("Must be data url")
        data = uri.split(",")[1]
        mime_type = uri.split(";")[0].split(":")[1]
        return cls(data, mime_type)


class MessageContent:
    def __init__(self, text: str, media: list[MessageContentMedia] = []) -> None:
        self.text: str = text
        self.media: list[MessageContentMedia] = media


class ChatMessage:
    lcMessageMapping: dict[str, t.Type[AIMessage | SystemMessage | HumanMessage]] = {
        "ai": AIMessage,
        "system": SystemMessage,
        "human": HumanMessage
    }

    def __init__(self, role: t.Literal["ai", "human", "system"], content: MessageContent | str) -> None:
        self.role: t.Literal["ai", "human", "system"] = role
        if isinstance(content, MessageContent):
            self.content: MessageContent = content
        else:
            self.content: MessageContent = MessageContent(str(content))

    @property
    def message_list(self) -> list[dict[str, t.Any]]:
        """Return the human message list in the format of langchain template message"""

        msg_list = [{
            "type": "text",
            "text": str(self.content.text)
        }] + [image.as_lcMessageDict for image in self.content.media]
        print("returning message list" + str(msg_list))
        return msg_list

    @property
    def lcMessage(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
        return self.lcMessageMapping[self.role](content=self.message_list)  # type: ignore
