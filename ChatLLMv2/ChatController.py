import logging
import hashlib
import datetime
import typing as t
import sqlalchemy.orm as so

from .DataHandler import (
    ChatRecord,
    ChatMessage
)
from .ChatModel.Base import BaseModel


logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class ChatController:
    """Controller class for managing chats."""
    _chat: ChatRecord

    def __init__(self,
                 dbSession: so.Session,
                 llmModel: BaseModel,
                 chatId: t.Optional[str] = None,
                 ) -> None:
        """
        Initialize a ChatController instance.

        :param dbSession: The sqlalchemy database session.
        :param llmModel: The language model to use for generating responses.
        :param chatId: The unique identifier for the chat.
        """
        logger.info(f"Initializing {__name__}")
        self.dbSession = dbSession
        self._chatId = chatId or hashlib.md5(str(datetime.datetime.now(datetime.UTC)).encode()).hexdigest()
        self.llmModel = llmModel
        self.chatInited = False  # to prevent hitting db when this just got inited

    def _initialize_chat(self) -> None:
        """Initialize the chat record if not already initialized."""
        logger.info("_initialize_chat invoking")
        logger.debug(f"Checking if current chat instance is initialized: {self.chatInited=}")
        if self.chatInited:
            logger.debug(f"{self.chatInited=} Initialized, skipping")
            return

        logger.info(f"Initializing chat record for chatId: {self._chatId}")
        self._chat = ChatRecord.init(chatId=self._chatId, dbSession=self.dbSession)

        logger.info(f"setting: {self._chatId=} to initialized")
        self.chatInited = True

    @property
    def chatId(self) -> str:
        """
        Get the chat ID.

        :return: The chat ID.
        """
        logger.debug("Getting Chat ID, Invoking _initialize_chat()")
        self._initialize_chat()

        logger.debug(f"Returning Chat ID {self._chatId} after _initialize_chat()")
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        """
        Set the chat ID and reinitialize the chat record.

        :param value: The new chat ID.
        """
        logger.debug(f"Setting ChatID:{value}")
        self._chatId = value

        logger.debug(f"Marking ChatID:{value} initialization to False")
        self.chatInited = False

        logger.debug(f"Invoking  _initialize_chat() for ChatID:{value}")
        self._initialize_chat()

    @property
    def currentChatRecords(self) -> ChatRecord:
        """
        Get the current chat record.

        :return: The current chat record.
        """
        logger.debug(f"Getter currentChatRecords Invoked for {self._chat.id=}, invoking _initialize_chat()")
        self._initialize_chat()

        logger.debug(f"Returning {self._chat.id=}")
        return self._chat

    def invokeLLM(self,
                  message: ChatMessage,
                  ) -> ChatMessage:
        """
        Invoke the language model with a user message and get the AI response.

        :param message: The new user message.
        :param contexts: A list of contexts for the message.
        :return: The AI response message.
        """
        logger.info(f"Invoking LLM: Message: {message.text[:10]=}, Invoking _initialize_chat()")
        self._initialize_chat()

        logger.debug(f"Checking if Message: {message.text[:10]=} is Empty with {message.text.strip()[:10]=}")
        if not message.text.strip():
            logger.debug(f"Message: {message.text[:10]=} is Empty {message.text.strip()=}")
            return ChatMessage('system', "Please provide a message.")

        logger.debug(f"Adding Message: {message.text[:10]=} to current referenced chat")
        self._chat.add_message(message)

        logger.debug(f"Invoking LlmModel with current chat:{self._chat.id=}")
        aiMessage = self.llmModel.invoke(self._chat)

        logger.debug(f"Got LlmModel Response:{aiMessage.text[:10]=}")
        self._chat.add_message(aiMessage)

        logger.debug(f"Saving changes of {self._chat.id=} to DB")
        self.dbSession.commit()

        logger.debug(f"Returning Response {aiMessage.text[:10]=}")
        return ChatMessage('ai', aiMessage.text)
