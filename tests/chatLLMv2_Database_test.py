import unittest
from ChatLLMv2.DataHandler import (
    ChatMessage,
    ChatRecord,
    TableBase,
)
from TestBase import TestBase


class DatabaseModel_Test(TestBase):

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
        self.assertTrue(self.session.query(ChatRecord).count() == 1)
        self.assertTrue(self.session.query(ChatMessage).count() == 2)

        retrieved_chat = self.session.query(ChatRecord).first()
        self.assertTrue(len(retrieved_chat.messages) == 2)  # type: ignore
        self.assertTrue(retrieved_chat.messages[0].text == "Test Text 1")  # type: ignore
        self.assertTrue(retrieved_chat.messages[1].text == "Test Text 2")  # type: ignore
        self.assertEqual(expected_chat_id, retrieved_chat.chatId)  # type: ignore


if __name__ == '__main__':
    unittest.main()

# TODO: make db check for all operation
