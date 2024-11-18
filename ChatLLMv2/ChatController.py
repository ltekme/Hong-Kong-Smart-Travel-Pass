import logging
from uuid import uuid4
import sqlalchemy.orm as so
from .ChatModel import *
from .ChatManager import *
from .ChatModel import *


logger = logging.getLogger(__name__)


class ChatController:
    _chat: ChatRecord

    def __init__(self,
                 dbSession: so.Session,
                 llmModel: BaseModel,
                 chatId: str = str(uuid4()),
                 ) -> None:
        logger.info(f"Initializing {__name__}")
        self.dbSession = dbSession
        self._chatId = chatId
        self.llmModel = llmModel
        self._chat = ChatRecord.init(chatId=self._chatId, dbSession=self.dbSession)

    @property
    def chatId(self) -> str:
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        self._chatId = value
        self._chat = ChatRecord.init(chatId=value, dbSession=self.dbSession)

    @property
    def currentChatRecord(self):
        return self._chat

    def invokeLLM(self, message: ChatMessage) -> ChatMessage:
        if not message.text:
            return ChatMessage('system', "Please provide a message.")
        self._chat.add_message(message)
        aiMessage = self.llmModel.invoke(self._chat)
        self._chat.add_message(aiMessage)
        self.dbSession.commit()
        return ChatMessage('ai', aiMessage.text)
