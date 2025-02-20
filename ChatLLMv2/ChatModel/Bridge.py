import logging

from langchain_core.language_models.chat_models import BaseChatModel

from .Base import BaseModel
from .Property import AdditionalLLMProperty
from ..DataHandler import ChatRecord, ChatMessage

from ChatLLM.Models import Chains as V1Chains
from ChatLLM.ChatRecord import ChatRecord as V1ChatRecord
from ChatLLM.ChatMessage import (
    MessageContentMedia as V1MessageContentMedia,
    MessageContent as V1MessageContent,
    ChatMessage as V1ChatMessage,
)

logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class v1Bridge(BaseModel):

    def __init__(self,
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalLLMProperty | None = None,
                 ) -> None:
        super().__init__(llm, additionalLLMProperty)
        logger.debug("Creating ChatLLMv1 Bridge")
        self.chainModel = V1Chains.LLMChainModel(llm=llm)
        if additionalLLMProperty is not None:
            self.chainModel.tools = additionalLLMProperty.llmTools

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        logger.debug("Recontricting ChatLLMv1 ChatRecord")
        v1ChatRecord = V1ChatRecord()
        for v2ChatMessages in chatRecord.messages:
            logger.debug(f"Converting {v2ChatMessages.id=}")

            v1MessageRole = "human" if v2ChatMessages.role == "user" else v2ChatMessages.role
            logger.debug(f"Converted ChatLLMv2 Message Role from {v2ChatMessages.role=}:{v1MessageRole=}")

            v1Attachments = list(map(lambda x: V1MessageContentMedia.from_uri(x.uri), v2ChatMessages.attachments))
            logger.debug(f"Remapped ChatLLMv2 Attachment to ChatLLMv1 MessageContentMedia")

            v1MessageContent = V1MessageContent(v2ChatMessages.text, v1Attachments)
            logger.debug(f"Created mapped ChatLLMv1 MessageContent")

            v1ChatMessage = V1ChatMessage(v1MessageRole, v1MessageContent)
            logger.debug(f"Created mapped ChatLLMv1 ChatMessage")

            v1ChatRecord.append(v1ChatMessage)
            logger.debug(f"Appended mapped ChatLLMv1 ChatMessage")

        logger.debug("Invoking ChatLLMv1 ChainModel with ChatLLMv1 ChatRecord")
        v1Response = self.chainModel.invoke(v1ChatRecord, "")

        logger.debug("Returning ChatLLMv1 ChainModel Response as ChatLLMv2 ChatMessage")
        return ChatMessage("ai", v1Response.content.text)  # type: ignore
