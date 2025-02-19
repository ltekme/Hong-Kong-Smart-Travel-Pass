import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..DataHandler import ChatRecord, ChatMessage
from .Base import BaseModel


logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class PureLLMModel(BaseModel):
    """Model class for pure language model interactions."""

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the language model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        logger.debug(f"Invoking llm")
        prompt = ChatPromptTemplate(messages=[
            MessagesPlaceholder('chat_history'),
        ])
        prompt_value = prompt.invoke({"chat_history": chatRecord.asLcMessages})  # type: ignore
        response = self.llm.invoke(prompt_value)  # type: ignore
        return ChatMessage("ai", str(response.content))  # type: ignore
