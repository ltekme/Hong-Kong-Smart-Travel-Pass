import logging
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel


from ..ChatManager import ChatRecord, ChatMessage

logger = logging.getLogger(__name__)


class BaseModel:
    """Base model class for language model interactions."""

    def __init__(self,
                 llm: BaseChatModel | None = None,
                 tools: list[BaseTool] = [],
                 overideChatContent: list[str] = [],
                 overideDirectOutput: bool = False,
                 ) -> None:
        """
        Initialize a BaseModel instance.

        :param llm: The language model to use.
        :param tools: A list of tools for the model to use.
        :param overideChatContent: A list of chat content to override.
        :param overideDirectOutput: Whether to directly output overide content.
        """
        self.llm = llm
        self.tools = tools
        self.overideChatContent = overideChatContent
        self.overideDirectOutput = overideDirectOutput

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        logger.debug(f"Invoking Base Mock Model")
        return ChatMessage("ai", f"MockMessage: {chatRecord.messages[-1].text}")
