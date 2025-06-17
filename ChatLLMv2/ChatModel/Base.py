import logging
import typing as t

from ..DataHandler import ChatRecord
from ..DataHandler import ChatMessage

from .Property import AdditionalModelProperty, InvokeContextValues

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
                 additionalLLMProperty: t.Optional[AdditionalModelProperty] = None,
                 ) -> None:
        """
        Initialize a BaseModel instance.

        :param additionalLLMProperty: Additional properties for the model, if any.
        """
        self.additionalLLMProperty = AdditionalModelProperty() if additionalLLMProperty is None else additionalLLMProperty

    def invoke(self, chatRecord: ChatRecord, contextValues: InvokeContextValues) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        logger.info(f"Invoking Base Mock Model with chatRecord: {chatRecord.chatId} and contextValues: {contextValues}")
        return ChatMessage("ai", f"MockMessage Respond: {chatRecord.messages[-1].text}")
