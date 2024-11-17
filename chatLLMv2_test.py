import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLMv2.ChatManager import *


class TestsBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)


class TestChatLLMv2DataBaseModel(TestsBase):

    def test_chat_record(self):
        TableBase.metadata.create_all(self.engine)

        message = ChatMessage(
            role="user",
            text="Test Text 1",
            attachments=[
                MessageAttachment(
                    type="media",
                    blob_name="1234"
                ),
                MessageAttachment(
                    type="media",
                    blob_name="2134"
                )
            ]
        )
        message1 = ChatMessage(
            role="ai",
            text="Test Text 2",
            attachments=[
                MessageAttachment(
                    type="media",
                    blob_name="2134"
                )
            ]
        )
        chat = ChatRecord()
        chat.messages = [message, message1]
        self.session.add_all([chat])
        self.session.commit()

        # append chatsattachment1 = Model.ContentAttachment()
        self.assertTrue(self.session.query(ChatRecord).count() == 1)
        self.assertTrue(self.session.query(ChatMessage).count() == 2)
        self.assertTrue(self.session.query(MessageAttachment).count() == 3)

        retrieved_chat = self.session.query(ChatRecord).first()
        self.assertTrue(len(retrieved_chat.messages) == 2)  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].text == "Test Text 1")  # type: ignore
        self.assertTrue(retrieved_chat.messages[1].text == "Test Text 2")  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].attachments[0].blob_name == "1234")  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].attachments[1].blob_name == "2134")  # type: ignore


class ChatRecord_Test(TestsBase):

    def setUp(self) -> None:
        self.chatRecord = ChatRecord()
        self.chatRecord.chatId = "testChatId"

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
            role="ai",  # type: ignore
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


if __name__ == '__main__':
    unittest.main()
