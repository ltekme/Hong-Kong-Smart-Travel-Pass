import os
import json
import uuid
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import tool

from google.oauth2.service_account import Credentials


class ChatLLM:
    chatRecordSchema = {
        "role": "ai" or "user",
        "message": "string",
    }

    _chatRecords = []

    def __init__(self,
                 credentials: Credentials,
                 model: str = "gemini-1.0-pro-vision",
                 temperature: float = 0.9,
                 max_tokens: int = 2048,
                 chatRecordFolderPath: str = './chat_record',
                 chatId: str = str(uuid.uuid4())):
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
        self._chatId = chatId
        self.chatRecordFolderPath = chatRecordFolderPath
        if not os.path.exists(chatRecordFolderPath):
            os.makedirs(chatRecordFolderPath)

    @property
    def chatRecordFilePath(self) -> str:
        return self.chatRecordFolderPath + "/" + self._chatId + ".json"

    @property
    def chatRecords(self) -> list:
        if self._chatRecords != []:
            return self._chatRecords
        if os.path.exists(self.chatRecordFilePath):
            with open(self.chatRecordFilePath, 'r') as f:
                records = json.load(f)
        return records or []

    @property
    def chatId(self) -> str:
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        self._chatId = value

    def save(self) -> None:
        if not os.path.exists(self.chatRecordFolderPath):
            os.makedirs(self.chatRecordFolderPath)
        if self._chatRecords != [] and self._chatRecords[-1]['role'] != "ai":
            raise ValueError("role must be different from the last record")
        if self._chatRecords == []:
            return
        with open(self.chatRecordFilePath, 'w') as f:
            json.dump(self._chatRecords, f, indent=4)

    def appendChatRecord(self, role: str, message: str) -> None:
        if self._chatRecords == []:
            self._chatRecords = self.chatRecords
        if role not in ["ai", "user"]:
            raise ValueError("role must be 'ai' or 'user'")
        if self.chatRecords != [] and self.chatRecords[-1]['role'] == role:
            raise ValueError("role must be different from the last record")
        self._chatRecords.append({
            "role": role,
            "message": message,
        })

    def new_message(self, message: str) -> dict:
        resault = self.llm.invoke(message)
        self.appendChatRecord('user', message)
        self.appendChatRecord('ai', resault.content)
        self.save()
        return {
            "message": resault.content,
            "chatId": self._chatId,
        }


if __name__ == "__main__":
    credentialsFiles = list(filter(lambda f: f.startswith(
        'gcp_cred') and f.endswith('.json'), os.listdir('.')))
    credentials = Credentials.from_service_account_file(
        credentialsFiles[0])
    chatLLM = ChatLLM(credentials)
    # chatLLM.chatId = "6c9bd85f-cc15-4f24-93cf-698f36fb8db1"
    print(chatLLM.new_message("Hello, World!"))
