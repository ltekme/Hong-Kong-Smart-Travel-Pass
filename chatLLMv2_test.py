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


class TestMessageAttachment(TestsBase):

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


if __name__ == '__main__':
    unittest.main()
