import os
import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import DatabaseModel
from ChatLLMv2.ChatManager import ChatManager
from ChatLLMv2.ChatRecord import ChatRecord


class TestChatLLMv2DataBaseModel(unittest.TestCase):

    def setUp(self):
        engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.db = so.Session(engine)
        DatabaseModel.Base.metadata.create_all(engine)

        attachment1 = DatabaseModel.ContentAttachment()
        attachment1.type = "media"
        attachment1.blob_name = "1234"
        message_content = DatabaseModel.MessageContent()
        message_content.text = "Test Text 1"
        message_content.attachments = [attachment1]
        message_content2 = DatabaseModel.MessageContent()
        message_content2.text = "Test Text 2"
        message = DatabaseModel.Message()
        message.role = "user"
        message.content = message_content
        message1 = DatabaseModel.Message()
        message1.role = "ai"
        message1.content = message_content2
        chat = DatabaseModel.Chat()
        chat.messages = [message, message1]
        self.db.add_all([chat])
        self.db.commit()

    def test_chat_record(self):
        # append chatsattachment1 = Model.ContentAttachment()
        self.assertTrue(self.db.query(DatabaseModel.Chat).count() == 1)
        self.assertTrue(self.db.query(DatabaseModel.Message).count() == 2)
        self.assertTrue(self.db.query(DatabaseModel.MessageContent).count() == 2)
        self.assertTrue(self.db.query(DatabaseModel.ContentAttachment).count() == 1)

        retrieved_chat = self.db.query(DatabaseModel.Chat).first()
        self.assertTrue(len(retrieved_chat.messages) == 2)  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].content.text == "Test Text 1")  # type: ignore
        self.assertTrue(retrieved_chat.messages[1].content.text == "Test Text 2")  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].content.attachments[0].blob_name == "1234")  # type: ignore


class ChatManager_Database_Test(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)

    def test_initialization_new_chat(self):
        DatabaseModel.Base.metadata.create_all(self.engine)

        chat_manager = ChatManager(database_session=self.session)
        self.assertIsNotNone(chat_manager.chat)
        self.assertTrue(self.session.query(ChatRecord).count() == 1)

    def test_initialization_existing_chat(self):
        DatabaseModel.Base.metadata.create_all(self.engine)

        existingChat = ChatRecord()
        existingChat.chatId = "test1234"
        self.session.add(existingChat)
        self.session.commit()

        chat_manager = ChatManager(database_session=self.session, chatId=existingChat.chatId)
        self.assertEqual(chat_manager.chat.chatId, existingChat.chatId)

    def test_error_on_null_database(self):
        if os.path.exists("./must_not_exist.db"):
            os.remove("must_not_exist.db")
        engine = sa.create_engine("sqlite:///must_not_exist.db", echo=True)
        session = so.Session(bind=engine)
        self.assertRaises(Exception, ChatManager, database_session=session, chatId="dummy")


if __name__ == '__main__':
    unittest.main()
