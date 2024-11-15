import uuid
import os
from .Models import *
from .Tools import *
from .ChatRecord import *
from .ChatMessage import *
from .UserProfile import *


class ChatManager:
    chatRecords = ChatRecord(
        system_message_string=("")
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())
    _profile: UserProfile | None = None

    def __init__(self,
                 llm_model: LLMModelBase,
                 chatId: str = "",
                 chatRecordFolderPath: str = './chat_data',
                 store_chat_records: bool = True
                 ) -> None:
        self.llm_model = llm_model
        self._chatId = chatId or self._chatId
        self.chatRecordFolderPath = chatRecordFolderPath
        self.store_chat_records = store_chat_records
        if store_chat_records and not os.path.exists(self.chatRecordFolderPath):
            os.makedirs(self.chatRecordFolderPath)
        if store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatId(self) -> str:
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        self._chatId = value
        if self.store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def profile(self) -> UserProfile | None:
        return self._profile

    @profile.setter
    def profile(self, value: UserProfile) -> None:
        self._profile = value

    @property
    def chatRecordFilePath(self) -> str:
        return self.chatRecordFolderPath + "/" + self._chatId + ".json"

    def new_message(self, message: str, media: list[MessageContentMedia] = [], context: str = "") -> ChatMessage:
        if not message:
            return ChatMessage('system', "Please provide a message.")
        user_message = ChatMessage('human', MessageContent(message, media))
        self.chatRecords.append(user_message)
        ai_message = self.llm_model.invoke(self.chatRecords, context)
        self.chatRecords.append(ai_message)

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return ChatMessage('ai', ai_message.content.text)
