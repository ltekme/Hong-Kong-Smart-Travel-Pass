import os
import unittest
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials
from ChatLLMv2.ChatModel.Base import BaseModel
from ChatLLMv2.ChatModel.PureLLM import PureLLMModel
from ChatLLMv2.ChatModel.Graph import GraphModel
from ChatLLMv2.DataHandler import (
    ChatMessage,
    ChatRecord,
)
from TestBase import TestBase


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


class GraphModel_Test(TestBase):
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
        model = GraphModel(llm=llm)
        chatRecord = ChatRecord("1324", messages=[
            ChatMessage("user", "hello")
        ])
        response = model.invoke(chatRecord)
        self.assertEqual(response.role, "ai")
        self.assertGreaterEqual(len(response.text), 5)


if __name__ == '__main__':
    unittest.main()
