import logging
from langchain_core.language_models.chat_models import BaseChatModel

from ..DataHandler import (
    ChatRecord,
    ChatMessage,
)

from .Property import AdditionalLLMProperty

logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class BaseModel:
    """Base model class for language model interactions."""

    def __init__(self,
                 llm: BaseChatModel | None = None,
                 additionalLLMProperty: AdditionalLLMProperty | None = None,
                 ) -> None:
        """
        Initialize a BaseModel instance.

        :param llm: The language model to use.
        :param tools: A list of tools for the model to use.
        """
        self.llm = llm
        if additionalLLMProperty is None:
            self.additionalLLMProperty = AdditionalLLMProperty()

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        logger.debug(f"Invoking Base Mock Model")
        return ChatMessage("ai", f"MockMessage: {chatRecord.messages[-1].text}")
