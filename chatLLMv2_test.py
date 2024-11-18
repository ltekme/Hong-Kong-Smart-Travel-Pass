import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so
from ChatLLMv2.ChatModel import *
from ChatLLMv2.ChatManager import *
from ChatLLMv2.ChatController import *
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials


class TestsBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)


class DatabaseModel_Test(TestsBase):

    def test_chat_record(self):
        TableBase.metadata.create_all(self.engine)
        expected_chat_id = "1234chat1234"
        self.session.add_all([
            ChatRecord(
                chatId=expected_chat_id,
                messages=[
                    ChatMessage(
                        role="user",
                        text="Test Text 1",
                        attachments=[]
                    ),
                    ChatMessage(
                        role="ai",
                        text="Test Text 2",
                        attachments=[]
                    )
                ]
            ),
        ])
        self.session.commit()

        # append chatsattachment1 = Model.ContentAttachment()
        self.assertTrue(self.session.query(ChatRecord).count() == 1)
        self.assertTrue(self.session.query(ChatMessage).count() == 2)

        retrieved_chat = self.session.query(ChatRecord).first()
        self.assertTrue(len(retrieved_chat.messages) == 2)  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].text == "Test Text 1")  # type: ignore
        self.assertTrue(retrieved_chat.messages[1].text == "Test Text 2")  # type: ignore
        self.assertEqual(expected_chat_id, retrieved_chat.chatId)  # type: ignore


class ChatRecord_Test(TestsBase):

    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)
        self.chatRecord = ChatRecord(chatId="testChatId")

    def test_add_valid_user_message(self):
        self.chatRecord.add_message(ChatMessage(
            role="user",
            text="Hello"
        ))
        self.chatRecord.add_message(ChatMessage(
            role="ai",
            text="Hello"
        ))
        self.chatRecord.add_message(ChatMessage(
            role="user",
            text="Hello Again"
        ))
        self.chatRecord.add_message(ChatMessage(
            role="ai",
            text="Hello To You"
        ))
        self.assertEqual(len(self.chatRecord.messages), 4)
        self.assertEqual(self.chatRecord.messages[0].role, "user")
        self.assertEqual(self.chatRecord.messages[2].role, "user")

    def test_add_invalid_role_message(self):
        message = ChatMessage(
            role="invalid_role",  # type: ignore
            text="Hello"
        )
        self.assertRaises(ValueError, self.chatRecord.add_message, message)

    def test_add_ai_message_first(self):
        message = ChatMessage(
            role="ai",
            text="Hello"
        )
        self.assertRaises(ValueError, self.chatRecord.add_message, message)

    def test_add_consecutive_ai_messages(self):
        self.chatRecord.add_message(ChatMessage(
            role="user",
            text="Hello"
        ))
        self.chatRecord.add_message(ChatMessage(
            role="ai",
            text="Hi"
        ))
        invalid_msg = ChatMessage(
            role="ai",
            text="How are you?"
        )
        self.assertRaises(ValueError, self.chatRecord.add_message, invalid_msg)

    def test_add_consecutive_user_messages(self):
        self.chatRecord.add_message(ChatMessage(
            role="user",
            text="Hello"
        ))
        invalid_message = ChatMessage(
            role="user",
            text="Hi"
        )
        self.assertRaises(ValueError, self.chatRecord.add_message, invalid_message)

    def test_message_append(self):
        TableBase.metadata.create_all(self.engine)
        expected_chat_id = "1234chat1234"
        chat = ChatRecord.init(self.session, expected_chat_id)
        chat.add_message(ChatMessage("user", "abc"))
        chat.add_message(ChatMessage("ai", "ai_abc"))
        self.session.commit()

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == expected_chat_id).first()
        self.assertEqual(retrieved_chat.messages[0].text, "abc")  # type: ignore
        self.assertEqual(retrieved_chat.messages[1].text, "ai_abc")  # type: ignore

        chat = ChatRecord.init(self.session, expected_chat_id)
        chat.add_message(ChatMessage("user", "abc2"))
        chat.add_message(ChatMessage("ai", "ai_abc2"))
        self.session.commit()

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == expected_chat_id).first()
        self.assertEqual(retrieved_chat.messages[0].text, "abc")  # type: ignore
        self.assertEqual(retrieved_chat.messages[1].text, "ai_abc")  # type: ignore
        self.assertEqual(retrieved_chat.messages[2].text, "abc2")  # type: ignore
        self.assertEqual(retrieved_chat.messages[3].text, "ai_abc2")  # type: ignore

    def test_chat_init(self):
        TableBase.metadata.create_all(self.engine)
        expected_chat_id = "1234chat1234"
        chat = ChatRecord.init(self.session, expected_chat_id)
        self.session.commit()
        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == expected_chat_id).first()
        self.assertEqual(chat, retrieved_chat)


class MessageAttachment_Test(TestsBase):

    def test_init_valid_data_url(self):
        data_url = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
        attachment = MessageAttachment(data_url)
        self.assertEqual(attachment.mime_type, "text/plain")
        self.assertEqual(attachment.base64Data, "SGVsbG8sIFdvcmxkIQ==")

    def test_init_invalid_data_url(self):
        data_url = "invalid_data_url"
        with self.assertRaises(ValueError):
            MessageAttachment(data_url)

    def test_base64Data_getter(self):
        data_url = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
        attachment = MessageAttachment(data_url)
        self.assertEqual(attachment.base64Data, "SGVsbG8sIFdvcmxkIQ==")

    def test_base64Data_setter(self):
        data_url = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
        attachment = MessageAttachment(data_url)
        new_data = "SGVsbG8sIFRlc3Qh"
        attachment.base64Data = new_data
        self.assertEqual(attachment.base64Data, new_data)

    def test_asLcMessageDict(self):
        data_url = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
        attachment = MessageAttachment(data_url)
        expected_dict = {
            "type": "media",
            "data": "SGVsbG8sIFdvcmxkIQ==",
            "mime_type": "text/plain",
        }
        self.assertEqual(attachment.asLcMessageDict, expected_dict)

    def test_save_and_retrieve_attachment(self):
        TableBase.metadata.create_all(self.engine)
        self.session.add(ChatRecord(
            chatId="1234t1",
            messages=[
                ChatMessage("user", "Hi", attachments=[
                    MessageAttachment("data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==")
                ])
            ]
        ))
        self.session.commit()

        retrieved_attachment = self.session.query(MessageAttachment).first()
        self.assertEqual(retrieved_attachment.mime_type, "text/plain")  # type: ignore
        self.assertEqual(retrieved_attachment.base64Data, "SGVsbG8sIFdvcmxkIQ==")  # type: ignore


class ChatController_Test(TestsBase):

    def test_get_chat_from_db(self):
        TableBase.metadata.create_all(self.engine)
        self.session.add(ChatRecord(chatId='test1', messages=[
            ChatMessage("user", "hi"),
            ChatMessage("ai", "Hello")
        ]))
        self.session.add(ChatRecord(chatId='test2', messages=[
            ChatMessage("user", "hi2"),
            ChatMessage("ai", "Hello2")
        ]))
        self.session.commit()
        model = BaseModel()
        chatController = ChatController(self.session, model, "test1")
        chatController2 = ChatController(self.session, model, "test2")
        self.assertEqual(chatController.currentChatRecord.messages[0].text, "hi")
        self.assertEqual(chatController.currentChatRecord.messages[1].text, "Hello")
        self.assertEqual(chatController2.currentChatRecord.messages[0].text, "hi2")
        self.assertEqual(chatController2.currentChatRecord.messages[1].text, "Hello2")

    def test_chatId_set(self):
        TableBase.metadata.create_all(self.engine)
        self.session.add(ChatRecord(chatId='test1', messages=[
            ChatMessage("user", "hi"),
            ChatMessage("ai", "Hello")
        ]))
        self.session.add(ChatRecord(chatId='test2', messages=[
            ChatMessage("user", "hi2"),
            ChatMessage("ai", "Hello2")
        ]))
        self.session.commit()
        model = BaseModel()
        chatController = ChatController(self.session, model, "test1")
        self.assertEqual(chatController.currentChatRecord.messages[0].text, "hi")
        chatController.chatId = "test2"
        self.assertEqual(chatController.currentChatRecord.messages[0].text, "hi2")

    def test_llm_invoke(self):
        TableBase.metadata.create_all(self.engine)

        model = BaseModel()
        chatController = ChatController(self.session, model, "test1")
        chatController.invokeLLM(ChatMessage("user", "hello"))
        self.assertEqual(chatController.currentChatRecord.messages[0].text, "hello")
        self.assertEqual(chatController.currentChatRecord.messages[1].text, "MockMessage: hello")

        chatController2 = ChatController(self.session, model, "test1")
        chatController2.invokeLLM(ChatMessage("user", "hello2"))
        chatController2.invokeLLM(ChatMessage("user", "hello3"))
        self.assertEqual(chatController.currentChatRecord.messages[0].text, "hello")
        self.assertEqual(chatController.currentChatRecord.messages[1].text, "MockMessage: hello")
        self.assertEqual(chatController.currentChatRecord.messages[2].text, "hello2")
        self.assertEqual(chatController.currentChatRecord.messages[3].text, "MockMessage: hello2")
        self.assertEqual(chatController.currentChatRecord.messages[4].text, "hello3")
        self.assertEqual(chatController.currentChatRecord.messages[5].text, "MockMessage: hello3")

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == "test1").first()
        self.assertEqual(len(chatController2.currentChatRecord.messages), len(retrieved_chat.messages))  # type: ignore


class ChatModel_BaseModel_Test(TestsBase):
    # I don't see a reason to have this, but sure
    def test_invoke(self):
        model = BaseModel()
        chatRecord = ChatRecord("1324", messages=[
            ChatMessage("user", "hello")
        ])
        self.assertEqual(model.invoke(chatRecord).text, "MockMessage: hello")


class ChatModel_PureLLMModel_Test(TestsBase):
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

# TODO: add tests for Message Context
