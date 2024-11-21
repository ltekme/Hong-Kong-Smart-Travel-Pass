import os
import base64
import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so
from PIL import Image
from io import BytesIO
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ChatLLMv2.ChatManager import (
    ChatMessage,
    ChatRecord,
    MessageContext,
    MessageAttachment,
    TableBase
)


class TestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)


class ChatRecord_Test(TestBase):

    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)
        self.chatRecord = ChatRecord(chatId="testChatId")

    def test_add_valid_user_message(self):
        self.chatRecord.add_message(ChatMessage("user", "Hello"))
        self.chatRecord.add_message(ChatMessage("ai", "Hello"))
        self.chatRecord.add_message(ChatMessage("user", "Hello Again"))
        self.chatRecord.add_message(ChatMessage("ai", "Hello To You"))
        self.assertEqual(len(self.chatRecord.messages), 4)
        self.assertEqual(self.chatRecord.messages[0].role, "user")
        self.assertEqual(self.chatRecord.messages[2].role, "user")

    def test_add_invalid_role_message(self):
        message = ChatMessage("invalid_role", "Hello")  # type: ignore
        expectedExeception = 'message role must be one of ["user", "system", "ai"]'
        with self.assertRaises(ValueError) as ve:
            self.chatRecord.add_message(message)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_add_ai_message_first(self):
        message = ChatMessage("ai", "Hello")
        expectedExeception = 'Cannot append message role=AI on the first message'
        with self.assertRaises(ValueError) as ve:
            self.chatRecord.add_message(message)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_add_consecutive_ai_messages(self):
        self.chatRecord.add_message(ChatMessage("user", "Hello"))
        self.chatRecord.add_message(ChatMessage("ai", "Hi"))
        invalidMessage = ChatMessage("ai", "How are you?")
        expectedExeception = 'Cannot have consective AI message'
        with self.assertRaises(ValueError) as ve:
            self.chatRecord.add_message(invalidMessage)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_add_consecutive_user_messages(self):
        self.chatRecord.add_message(ChatMessage("user", "Hello"))
        invalidMessage = ChatMessage("user", "Hi")
        expectedExeception = 'Cannot have consective USER message'
        with self.assertRaises(ValueError) as ve:
            self.chatRecord.add_message(invalidMessage)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_message_append(self):
        TableBase.metadata.create_all(self.engine)
        expected_chat_id = "1234chat1234"
        chat = ChatRecord.init(self.session, expected_chat_id)
        chat.add_message(ChatMessage("user", "abc"))
        chat.add_message(ChatMessage("ai", "ai_abc"))
        self.session.commit()

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == expected_chat_id).first()
        self.assertIsNotNone(retrieved_chat)
        self.assertEqual(retrieved_chat.messages[0].text, "abc")  # type: ignore
        self.assertEqual(retrieved_chat.messages[1].text, "ai_abc")  # type: ignore

        chat = ChatRecord.init(self.session, expected_chat_id)
        chat.add_message(ChatMessage("user", "abc2"))
        chat.add_message(ChatMessage("ai", "ai_abc2"))
        self.session.commit()

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == expected_chat_id).first()
        self.assertIsNotNone(retrieved_chat)
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

    def test_asLcMessages_output(self):
        chatMessage1 = ChatMessage('user', "hello1")
        chatMessage2 = ChatMessage('ai', "hello2")
        chatMessage3 = ChatMessage('user', "hello3")
        chatMessage4 = ChatMessage('ai', "hello4")
        chatRecord = ChatRecord("1234", messages=[
            chatMessage1,
            chatMessage2,
            chatMessage3,
            chatMessage4,
        ])
        self.assertListEqual(chatRecord.asLcMessages, [
            HumanMessage([{'type': 'text', 'text': 'hello1'}]),
            AIMessage([{'type': 'text', 'text': 'hello2'}]),
            HumanMessage([{'type': 'text', 'text': 'hello3'}]),
            AIMessage([{'type': 'text', 'text': 'hello4'}]),
        ])


class MessageAttachment_Test(TestBase):

    def test_init_dataUrl(self):
        data = "SGVsbG8sIFdvcmxkIQ=="
        dataUrl = f"data:text/plain;base64,{data}"
        attachment = MessageAttachment(dataUrl)
        self.assertEqual(attachment.mimeType, "text/plain")
        self.assertEqual(attachment.base64Data, data)
        self.assertEqual(attachment.asLcMessageDict, {
            "type": "media",
            "data": data,
            "mime_type": "text/plain",
        })

    def test_base64Data_getter(self):
        data = "SGVsbG8sIFdvcmxkIQ=="
        dataUrl = f"data:text/plain;base64,{data}"
        attachment = MessageAttachment(dataUrl)
        self.assertEqual(attachment.mimeType, "text/plain")
        self.assertEqual(attachment.base64Data, data)
        self.assertEqual(attachment.asLcMessageDict, {
            "type": "media",
            "data": data,
            "mime_type": "text/plain",
        })

    def test_base64Data_setter(self):
        data = "SGVsbG8sIFdvcmxkIQ=="
        dataUrl = f"data:text/plain;base64,{data}"
        attachment = MessageAttachment(dataUrl)
        newData = "SGVsbG8sIFRlc3Qh"
        attachment.base64Data = newData
        self.assertEqual(attachment.mimeType, "text/plain")
        self.assertEqual(attachment.base64Data, newData)
        self.assertEqual(attachment.asLcMessageDict, {
            "type": "media",
            "data": newData,
            "mime_type": "text/plain",
        })

    def test_imageLoad_ico(self):
        # this ico file is semi broken
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/cat.ico"), 'rb') as f:
            imageDataUrl = f"data:image/x-icon;base64,{base64.b64encode(f.read()).decode('ascii')}"
        attachment = MessageAttachment(imageDataUrl)

        processedData = BytesIO()
        im = Image.open(BytesIO(base64.b64decode(imageDataUrl.split(",")[1])))
        im.save(processedData, "png")
        base64ProcessedData = base64.b64encode(processedData.getvalue()).decode()

        self.assertEqual(attachment.mimeType, "image/png")
        self.assertEqual(attachment.base64Data, base64ProcessedData)
        self.assertEqual(attachment.asLcMessageDict, {
            "type": "media",
            "data": base64ProcessedData,
            "mime_type": "image/png",
        })

    def test_imageLoad_gif(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/cat.gif"), 'rb') as f:
            imageDataUrl = f"data:image/gif;base64,{base64.b64encode(f.read()).decode('ascii')}"
        attachment = MessageAttachment(imageDataUrl)
        self.assertEqual(attachment.mimeType, "image/gif")
        self.assertEqual(attachment.base64Data, imageDataUrl.split(",")[1])
        self.assertEqual(attachment.asLcMessageDict, {
            "type": "media",
            "data": imageDataUrl.split(",")[1],
            "mime_type": "image/gif",
        })

    def test_invalid_data_url(self):
        dataUrl = "invaliddataurl"
        expectedExeception = "dataUrl must be a javascript data URL"
        with self.assertRaises(ValueError) as ve:
            MessageAttachment(dataUrl)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_invalid_image_data(self):
        dataUrl = "data:image/png;base64,invalidbase64data"
        expectedExeception = "Invalid image data"
        with self.assertRaises(ValueError) as ve:
            MessageAttachment(dataUrl)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_invalid_gif_data(self):
        dataUrl = "data:image/gif;base64,invalidbase64data"
        expectedExeception = "Invalid gif data"
        with self.assertRaises(ValueError) as ve:
            MessageAttachment(dataUrl)
        self.assertEqual(str(ve.exception), expectedExeception)


class MessageContext_Test(TestBase):
    def test_asText_outputs(self):
        context1 = MessageContext("testParam1", "testValue1")
        context2 = MessageContext("testParam2", "testValue2")
        context3 = MessageContext("testParam3", "testValue3")

        self.assertEqual(context1.asText, "testParam1: testValue1;")
        self.assertEqual(context2.asText, "testParam2: testValue2;")
        self.assertEqual(context3.asText, "testParam3: testValue3;")


class ChatMessage_Test(TestBase):

    def setUp(self):
        self.b64String1 = base64.b64encode("Hello World1".encode("ascii")).decode("ascii")
        self.b64String2 = base64.b64encode("Hello World2".encode("ascii")).decode("ascii")
        self.b64String3 = base64.b64encode("Hello World3".encode("ascii")).decode("ascii")
        self.b64String4 = base64.b64encode("Hello World4".encode("ascii")).decode("ascii")
        self.dataUrl1 = f"data:text/plain;base64,{self.b64String1}"
        self.dataUrl2 = f"data:text/plain;base64,{self.b64String2}"
        self.dataUrl3 = f"data:text/plain;base64,{self.b64String3}"
        self.dataUrl4 = f"data:text/plain;base64,{self.b64String4}"
        self.context1 = MessageContext("testParam1", "testValue1")
        self.context2 = MessageContext("testParam2", "testValue2")
        self.context3 = MessageContext("testParam3", "testValue3")
        self.context4 = MessageContext("testParam4", "testValue4")
        self.attachment1 = MessageAttachment(self.dataUrl1)
        self.attachment2 = MessageAttachment(self.dataUrl2)
        self.attachment3 = MessageAttachment(self.dataUrl3)
        self.attachment4 = MessageAttachment(self.dataUrl4)
        self.chatMessage1_sys = ChatMessage("system", "hello", [], [])
        self.chatMessage1_user = ChatMessage("user", "hello", [], [])
        self.chatMessage1_ai = ChatMessage("ai", "hello", [], [])
        self.chatMessage2 = ChatMessage("user", "hello", [], [
            self.context1,
            self.context2,
        ])
        self.chatMessage3 = ChatMessage("user", "hello", [
            self.attachment1,
            self.attachment2,
        ], [])
        self.chatMessage4 = ChatMessage("user", "hello", [
            self.attachment3,
            self.attachment4
        ], [
            self.context3,
            self.context4
        ])

    def test_asLcMessageList_output(self):
        self.assertListEqual(self.chatMessage1_user.asLcMessageList, [{
            "type": "text",
            "text": "hello"
        }])
        self.assertListEqual(self.chatMessage2.asLcMessageList, [{
            "type": "text",
            "text": "hello\n\nMessageContext << EOF\ntestParam1: testValue1;\ntestParam2: testValue2;\nEOF",
        }])
        self.assertListEqual(self.chatMessage3.asLcMessageList, [{
            "type": "text",
            "text": "hello"
        }, {
            "type": "media",
            "data": self.b64String1,
            "mime_type": self.dataUrl1.split(";")[0].split(":")[1],
        }, {
            "type": "media",
            "data": self.b64String2,
            "mime_type": self.dataUrl2.split(";")[0].split(":")[1],
        }])
        self.assertListEqual(self.chatMessage4.asLcMessageList, [{
            "type": "text",
            "text": "hello\n\nMessageContext << EOF\ntestParam3: testValue3;\ntestParam4: testValue4;\nEOF",
        }, {
            "type": "media",
            "data": self.b64String3,
            "mime_type": self.dataUrl3.split(";")[0].split(":")[1],
        }, {
            "type": "media",
            "data": self.b64String4,
            "mime_type": self.dataUrl4.split(";")[0].split(":")[1],
        }])

    def test_asLcMessageObject_output(self):
        self.assertEqual(self.chatMessage1_user.asLcMessageObject, HumanMessage([{
            "type": "text",
            "text": "hello"
        }]))
        self.assertEqual(self.chatMessage1_sys.asLcMessageObject, SystemMessage([{
            "type": "text",
            "text": "hello"
        }]))
        self.assertEqual(self.chatMessage1_ai.asLcMessageObject, AIMessage([{
            "type": "text",
            "text": "hello"
        }]))
        self.assertEqual(self.chatMessage2.asLcMessageObject, HumanMessage([{
            "type": "text",
            "text": "hello\n\nMessageContext << EOF\ntestParam1: testValue1;\ntestParam2: testValue2;\nEOF",
        }]))
        self.assertEqual(self.chatMessage3.asLcMessageObject, HumanMessage([{
            "type": "text",
            "text": "hello"
        }, {
            "type": "media",
            "data": self.b64String1,
            "mime_type": self.dataUrl1.split(";")[0].split(":")[1],
        }, {
            "type": "media",
            "data": self.b64String2,
            "mime_type": self.dataUrl2.split(";")[0].split(":")[1],
        }]))
        self.assertEqual(self.chatMessage4.asLcMessageObject, HumanMessage([{
            "type": "text",
            "text": "hello\n\nMessageContext << EOF\ntestParam3: testValue3;\ntestParam4: testValue4;\nEOF",
        }, {
            "type": "media",
            "data": self.b64String3,
            "mime_type": self.dataUrl3.split(";")[0].split(":")[1],
        }, {
            "type": "media",
            "data": self.b64String4,
            "mime_type": self.dataUrl4.split(";")[0].split(":")[1],
        }]))


if __name__ == '__main__':
    unittest.main()
