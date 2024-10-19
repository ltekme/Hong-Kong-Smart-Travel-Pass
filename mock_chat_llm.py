import os
import json
import uuid
import typing as t
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import tool

from google.oauth2.service_account import Credentials


class ChatMessage:

    def __init__(self, role: str, message: str, **kwargs) -> None:
        self.role = role
        self.message = message

    def prompt_message(self):
        if self.role == "ai":
            return AIMessage(self.message)
        elif self.role == "user":
            return HumanMessage(self.message)
        else:
            raise ValueError("role must be 'ai' or 'user'")

    def to_dict(self):
        return {
            "role": self.role,
            "message": self.message,
        }


class ChatMessages:

    _chat_messages: t.List[ChatMessage] = []

    def __init__(self) -> None:
        pass

    def get_all(self) -> list:
        return [chatMessage.to_dict() for chatMessage in self._chat_messages]

    def append(self, chatMessage: ChatMessage) -> None:
        self._chat_messages.append(chatMessage)

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump([chatMessage.to_dict()
                      for chatMessage in self._chat_messages], f, indent=4)

    def get_from_file(self, file_path: str) -> None:
        with open(file_path, 'r') as f:
            self._chat_messages = [ChatMessage(
                **chatMessage) for chatMessage in json.load(f)]


class ChatLLM:
    chatRecordSchema = {
        "role": "ai" or "user",
        "message": "string",
    }

    chatRecords = ChatMessages()
    chatRecordFolderPath = './chat_data'
    store_chat_records = True

    def __init__(self,
                 credentials: Credentials,
                 model: str = "gemini-1.0-pro-vision",
                 temperature: float = 0.9,
                 max_tokens: int = 2048,
                 chatRecordFolderPath: str = './chat_data',
                 chatId: str = str(uuid.uuid4()),
                 store_chat_records: bool = True):
        self.llm = ChatVertexAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=None,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        )
        self.chatId = chatId or str(uuid.uuid4())
        self.chatRecordFolderPath = chatRecordFolderPath
        self.store_chat_records = store_chat_records
        if store_chat_records and not os.path.exists(self.chatRecordFolderPath):
            os.makedirs(self.chatRecordFolderPath)
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatRecordFilePath(self) -> str:
        return self.chatRecordFolderPath + "/" + self.chatId + ".json"

    def new_message(self, message: str) -> dict:
        resault = self.llm.invoke(message)
        
        self.chatRecords.append(ChatMessage('user', message))
        self.chatRecords.append(ChatMessage('ai', resault.content))
        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return ChatMessage('ai', resault.content).to_dict()


if __name__ == "__main__":
    credentialsFiles = list(filter(lambda f: f.startswith(
        'gcp_cred') and f.endswith('.json'), os.listdir('.')))
    credentials = Credentials.from_service_account_file(
        credentialsFiles[0])
    chatLLM = ChatLLM(credentials)
    # chatLLM.chatId = "6c9bd85f-cc15-4f24-93cf-698f36fb8db1"
    print(chatLLM.new_message("Hello, World!"))
