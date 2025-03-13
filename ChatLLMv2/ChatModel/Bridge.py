import logging

from langchain_core.language_models.chat_models import BaseChatModel

from .Base import BaseModel
from .Property import AdditionalModelProperty
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


def remapV2ChatMessageeToV1ChatMessage(v2ChatMessages: ChatMessage) -> V1ChatMessage:
    """
    Remap V2 ChatMessage to V1 Chat Message

    :param v2ChatMessage: The v2 ChatMessage
    :return: V2ChatMessage
    """
    logger.info(f"Converting v2 ChatMessage on chat:{v2ChatMessages.chat_id=}, {v2ChatMessages.role=}:{v2ChatMessages.asLcMessageList=}")

    v1MessageRole = "human" if v2ChatMessages.role == "user" else v2ChatMessages.role
    logger.debug(f"Converted ChatLLMv2 Message Role from {v2ChatMessages.role=}:{v1MessageRole=}")

    v1Attachments = list(map(lambda x: V1MessageContentMedia.from_uri(x.uri), v2ChatMessages.attachments))
    logger.debug(f"Remapped ChatLLMv2 Attachment to ChatLLMv1 MessageContentMedia for {v2ChatMessages.chat_id=}")

    v1MessageContent = V1MessageContent(v2ChatMessages.text, v1Attachments)
    logger.debug(f"Created mapped ChatLLMv1 MessageContent for {v2ChatMessages.chat_id=}")

    v1ChatMessage = V1ChatMessage(v1MessageRole, v1MessageContent)
    logger.debug(f"Created mapped ChatLLMv1 ChatMessage for {v2ChatMessages.chat_id=}")

    return v1ChatMessage


class v1Bridge(BaseModel):

    def __init__(self,
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalModelProperty | None = None,
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
        logger.info(f"Recontricting ChatLLMv1 ChatRecord for {chatRecord.chatId=}")
        v1ChatMessages = list(map(remapV2ChatMessageeToV1ChatMessage, chatRecord.messages))

        logger.debug(f"Resaulting v1 Chat Messages: {list(map(lambda x: (x.role, x.content.text), v1ChatMessages))}")

        logger.debug(f"Setting up ChatLLMv1 ChatRecord for {chatRecord.chatId=}")
        v1ChatRecord = V1ChatRecord()

        logger.debug("Setting up information for v1 ChatRecord")
        v1ChatRecord.messages = v1ChatMessages

        logger.debug("Invoking ChatLLMv1 ChainModel with ChatLLMv1 ChatRecord")
        v1Response = self.chainModel.invoke(v1ChatRecord, "")

        logger.debug("Returning ChatLLMv1 ChainModel Response as ChatLLMv2 ChatMessage")
        return ChatMessage("ai", v1Response.content.text)  # type: ignore
