import logging
from uuid import uuid4
import sqlalchemy.orm as so
from .ChatModel import *
from .DataHandler import *
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
        self.chatInited = False  # to prevent hitting db when this just got inited

    def _initialize_chat(self):
        """Initialize the chat record if not already initialized."""
        if not self.chatInited:
            logger.info(f"Initializing chat record for chatId: {self._chatId}")
            self._chat = ChatRecord.init(chatId=self._chatId, dbSession=self.dbSession)
            self.chatInited = True

    @property
    def chatId(self) -> str:
        """
        Get the chat ID.

        :return: The chat ID.
        """
        self._initialize_chat()
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        """
        Set the chat ID and reinitialize the chat record.

        :param value: The new chat ID.
        """
        self._chatId = value
        self.chatInited = False
        self._initialize_chat()

    @property
    def currentChatRecords(self) -> ChatRecord:
        """
        Get the current chat record.

        :return: The current chat record.
        """
        self._initialize_chat()
        return self._chat

    def invokeLLM(self, message: ChatMessage, context: list[MessageContext] = []) -> ChatMessage:
        """
        Invoke the language model with a user message and get the AI response.

        :param message: The new user message.
        :param contexts: A list of contexts for the message.
        :return: The AI response message.
        """
        self._initialize_chat()
        if not message.text:
            return ChatMessage('system', "Please provide a message.")
        if context:
            contextList = list(map(lambda c: c.asText, context))
            self._chat.add_message(ChatMessage("system", f"""real-time context and information:\n{"\n".join(contextList)}"""))
        self._chat.add_message(message)
        aiMessage = self.llmModel.invoke(self._chat)
        self._chat.add_message(aiMessage)
        self.dbSession.commit()
        return ChatMessage('ai', aiMessage.text)
