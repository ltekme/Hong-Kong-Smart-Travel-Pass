import typing as t
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class MessageContentMedia:
    def __init__(self, format: str, data: str, media_type: str = "image") -> None:
        self.format: str = format
        self.data: str = data
        self.media_type: str = media_type

    @property
    def uri(self) -> str:
        return f"data:{self.media_type}/{self.format};base64,{self.data}"

    @property
    def as_lcMessageDict(self) -> dict[str, t.Any]:
        print("Converting to ")
        return {
            # "type": "image_url",
            # "image_url": {"url": self.uri}
            "type": "media",
            "data": self.data,
            "mime_type": f"{self.media_type}/{self.format}",
        }

    @staticmethod
    def from_uri(uri: str) -> t.Union["MessageContentMedia", None]:
        try:
            if not uri.startswith('data:'):
                pass
            header = uri.split(';')[0].split('/')
            format = header[1]
            media_type = header[0].split(':')[1]
            data = uri.split(',')[1]
            return MessageContentMedia(format=format, data=data, media_type=media_type)
        except Exception as e:
            print(f"Error encoding media {e}")
            return None


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
