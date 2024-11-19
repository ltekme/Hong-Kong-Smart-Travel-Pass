import os
import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials
from ChatLLMv2.ChatModel import (
    BaseModel,
    PureLLMModel,
)
from ChatLLMv2.ChatManager import (
    ChatMessage,
    ChatRecord,
)


class TestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)


class BaseModel_Test(TestBase):
    # I don't see a reason to have this, but sure
    def test_invoke(self):
        model = BaseModel()
        chatRecord = ChatRecord("1324", messages=[
            ChatMessage("user", "hello")
        ])
        self.assertEqual(model.invoke(chatRecord).text, "MockMessage: hello")


class PureLLMModel_Test(TestBase):
    def test_invoke(self):
        credentialsFiles = list(filter(lambda f: f.startswith(
            'gcp_cred') and f.endswith('.json'), os.listdir('.')))
        credentials = Credentials.from_service_account_file(  # type: ignore
            credentialsFiles[0])
        llm = ChatVertexAI(
            region="us-central1",
            model="gemini-1.5-flash-002",
            credentials=credentials,
            project=credentials.project_id,  # type: ignore
        )
        model = PureLLMModel(llm=llm)
        chatRecord = ChatRecord("1324", messages=[
            ChatMessage("user", "hello")
        ])
        self.assertEqual(model.invoke(chatRecord).role, "ai")


if __name__ == '__main__':
    unittest.main()
