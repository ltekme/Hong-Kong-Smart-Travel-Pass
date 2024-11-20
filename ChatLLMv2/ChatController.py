import logging
from uuid import uuid4
import sqlalchemy.orm as so
from .ChatModel import *
from .ChatManager import *
from .ChatModel import *


logger = logging.getLogger(__name__)


class ChatController:
    """Controller class for managing chats."""
    _chat: ChatRecord

    def __init__(self,
                 dbSession: so.Session,
                 llmModel: BaseModel,
                 chatId: str = str(uuid4()),
                 ) -> None:
        """
        Initialize a ChatController instance.

        :param dbSession: The sqlalchemy database session.
        :param llmModel: The language model to use for generating responses.
        :param chatId: The unique identifier for the chat.
        """
        logger.info(f"Initializing {__name__}")
        self.dbSession = dbSession
        self._chatId = chatId
        self.llmModel = llmModel
        self._chat = ChatRecord.init(chatId=self._chatId, dbSession=self.dbSession)

    @property
    def chatId(self) -> str:
        """
        Get the chat ID.

        :return: The chat ID.
        """
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        """
        Set the chat ID and reinitialize the chat record.

        :param value: The new chat ID.
        """
        self._chatId = value
        self._chat = ChatRecord.init(chatId=value, dbSession=self.dbSession)

    @property
    def currentChatRecords(self) -> ChatRecord:
        """
        Get the current chat record.

        :return: The current chat record.
        """
        return self._chat

    def invokeLLM(self, message: ChatMessage) -> ChatMessage:
        """
        Invoke the language model with a user message and get the AI response.

        :param message: The new user message.
        :return: The AI response message.
        """
        if not message.text:
            return ChatMessage('system', "Please provide a message.")
        self._chat.add_message(message)
        aiMessage = self.llmModel.invoke(self._chat)
        self._chat.add_message(aiMessage)
        self.dbSession.commit()
        return ChatMessage('ai', aiMessage.text)
