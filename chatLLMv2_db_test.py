import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2 import Model


class TestChatLLMv2DataBaseModel(unittest.TestCase):

    def setUp(self):
        engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.db = so.Session(engine)
        Model.Base.metadata.create_all(engine)

        attachment1 = Model.ContentAttachment()
        attachment1.type = "media"
        attachment1.blob_name = "1234"
        message_content = Model.MessageContent()
        message_content.text = "Test Text 1"
        message_content.attachments = [attachment1]
        message_content2 = Model.MessageContent()
        message_content2.text = "Test Text 2"
        message = Model.Message()
        message.role = "user"
        message.content = message_content
        message1 = Model.Message()
        message1.role = "ai"
        message1.content = message_content2
        chat = Model.Chat()
        chat.messages = [message, message1]
        self.db.add_all([chat])
        self.db.commit()

    def test_chat_record(self):
        # append chatsattachment1 = Model.ContentAttachment()
        self.assertTrue(self.db.query(Model.Chat).count() == 1)
        self.assertTrue(self.db.query(Model.Message).count() == 2)
        self.assertTrue(self.db.query(Model.MessageContent).count() == 2)
        self.assertTrue(self.db.query(Model.ContentAttachment).count() == 1)

        retrieved_chat = self.db.query(Model.Chat).first()
        self.assertTrue(len(retrieved_chat.messages) == 2)  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].content.text == "Test Text 1")  # type: ignore
        self.assertTrue(retrieved_chat.messages[1].content.text == "Test Text 2")  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].content.attachments[0].blob_name == "1234")  # type: ignore


if __name__ == '__main__':
    unittest.main()
