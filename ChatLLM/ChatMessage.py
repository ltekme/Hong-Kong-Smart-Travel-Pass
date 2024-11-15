import typing as t
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class MessageContentMedia:
    def __init__(self, data_uri: str) -> None:
        if not data_uri.startswith("data"):
            raise ValueError("Must be data url")
        self._data_uri: str = data_uri

    @property
    def uri(self) -> str:
        return self._data_uri

    @property
    def as_lcMessageDict(self) -> dict[str, t.Any]:
        print(self._data_uri.split(",")[1])
        return {
            # "type": "image_url",
            # "image_url": {"url": self.uri}
            "type": "media",
            "data": self._data_uri.split(",")[1],
            "mime_type": self._data_uri.split(";")[0].split(":")[1],
        }

    @staticmethod
    def from_uri(uri: str) -> t.Union["MessageContentMedia", None]:
        return MessageContentMedia(uri)


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
