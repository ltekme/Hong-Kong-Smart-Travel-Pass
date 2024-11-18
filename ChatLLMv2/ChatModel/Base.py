import logging
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel


from ..ChatManager import ChatRecord, ChatMessage

logger = logging.getLogger(__name__)


class BaseModel:
    def __init__(self,
                 # Not used in base mock
                 llm: BaseChatModel | None = None,
                 tools: list[BaseTool] = [],
                 overideChatContent: list[str] = [],
                 overideDirectOutput: bool = False,
                 ) -> None:
        self.llm = llm
        self.tools = tools
        self.overideChatContent = overideChatContent
        self.overideDirectOutput = overideDirectOutput

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        logger.debug(f"Invoking Base Mock Model")
        return ChatMessage("ai", f"MockMessage: {chatRecord.messages[-1].text}")
