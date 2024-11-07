import os
import json
import uuid
import copy
import base64
import typing as t
import datetime
import math
from time import sleep

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import BaseTool

from langchain.agents import create_structured_chat_agent, AgentExecutor  # type: ignore

from google.oauth2.service_account import Credentials

from llm_tools import LLMTools

from dotenv import load_dotenv
load_dotenv()


class MessageContentMedia:
    def __init__(self, format: str, data: str, media_type: str = "image") -> None:
        self.format = format
        self.data = data
        self.media_type = media_type

    @property
    def uri(self) -> str:
        return f"data:{self.media_type}/{self.format};base64,{self.data}"

    @property
    def as_lcMessageDict(self) -> dict[str, t.Any]:
        return {
            "type": "image_url",
            "image_url": {"url": self.uri}
        }

    @staticmethod
    def from_uri(uri: str) -> t.Union["MessageContentMedia", None]:
        try:
            if not uri.startswith('data:'):
                pass
            header = uri.split(';')[0].split('/')
            format = header[1]
            media_type = header[0].split(':')[1]
            data = uri.split(',')[1]
            return MessageContentMedia(format=format, data=data, media_type=media_type)
        except Exception as e:
            return None


class MessageContent:
    def __init__(self, text: str, media: list[MessageContentMedia] = []) -> None:
        self.text = text
        self.media = media


class Message:
    lcMessageMapping: dict[str, t.Type[AIMessage | SystemMessage | HumanMessage]] = {
        "ai": AIMessage,
        "system": SystemMessage,
        "human": HumanMessage
    }

    def __init__(self, role: t.Literal["ai", "human", "system"], content: MessageContent | str) -> None:
        self.role: t.Literal["ai", "human", "system"] = role
        if isinstance(content, MessageContent):
            self.content: MessageContent = content
        else:
            self.content: MessageContent = MessageContent(str(content))

    @property
    def message_list(self) -> list[dict[t.Any, t.Any]]:
        """Return the human message list in the format of langchain template message"""
        return [{
            "type": "text",
            "text": str(self.content.text)
        }] + [image.as_lcMessageDict for image in self.content.media]

    @property
    def lcMessage(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
        return self.lcMessageMapping[self.role](content=self.message_list)


class Chat:
    _chat_messages: list[Message] = []

    def __init__(self, system_message_string: str | None = None) -> None:
        if system_message_string:
            system_message_content = MessageContent(system_message_string)
            system_message = Message('system', system_message_content)
            self._chat_messages.append(system_message)

    @property
    def as_list(self) -> list[Message]:
        return self._chat_messages

    @property
    def as_list_of_lcMessages(self) -> list[HumanMessage | AIMessage | SystemMessage]:
        return [msg.lcMessage for msg in self._chat_messages]

    def append(self, message: Message) -> None:
        if not isinstance(message, Message):
            raise ValueError("message must be of type Message")
        if message.role not in ["ai", "human"]:
            raise ValueError("message role must be either 'ai' or 'human'")
        if self._chat_messages:
            last_role = self._chat_messages[-1].role
            if last_role == message.role:
                raise ValueError("message must be of different role")
        self._chat_messages.append(message)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w', encoding="utf-8-sig") as f:
            messages = [
                {"role": msg.role, "content": msg.message_list}
                for msg in self._chat_messages]
            json.dump(messages, f, indent=4, ensure_ascii=False)

    def get_from_file(self, file_path: str) -> list:
        system_message_copy = self.system_message
        try:
            with open(file_path, 'r', encoding="utf-8-sig") as f:
                data_in_file = json.load(f)

            messages = []
            for msg in data_in_file:
                message_content_text = None
                message_content_media = []

                for content in msg['content']:
                    if content['type'] == 'text':
                        message_content_text = content['text']
                    if content['type'] == 'image_url':
                        message_content_media.append(
                            MessageContentMedia.from_uri(content['image_url']['url']))

                messages.append(Message(
                    role=msg['role'],
                    content=MessageContent(
                        text=message_content_text if message_content_text else '',
                        media=message_content_media
                    ))
                )

            self._chat_messages = messages
            return self._chat_messages

        except FileNotFoundError:
            if system_message_copy is not None:
                self._chat_messages = [system_message_copy]
            return self._chat_messages

        except json.JSONDecodeError as e:
            if system_message_copy is not None:
                self._chat_messages = [system_message_copy]
            return self._chat_messages

    @property
    def system_message(self) -> Message | None:
        if self._chat_messages:
            if self._chat_messages[0].role != 'system':
                return None
            return self._chat_messages[0]
        return None

    @system_message.setter
    def system_message(self, value: str) -> None:
        if self._chat_messages:
            if self._chat_messages[0].role != 'system':
                self._chat_messages.insert(0, Message('system', value))
                return
            self._chat_messages[0].content = MessageContent(value)
        return None

    def remove_system_message(self) -> Message | None:
        if self._chat_messages:
            if self._chat_messages[0].role == 'system':
                return self._chat_messages.pop(0)
        return None

    @property
    def last_message(self) -> Message | None:
        if self._chat_messages:
            if self._chat_messages[-1].role != 'system':
                return self._chat_messages[-1]
        return None

    def remove_last_message(self) -> Message | None:
        if self._chat_messages:
            if self._chat_messages[-1].role != 'system':
                return self._chat_messages.pop(-1)
        return None


class LLMChainTools:
    def __init__(self, credentials: Credentials) -> None:
        self.credentials = credentials
        self.llm_tools = LLMTools(credentials=credentials, verbose=True)

    @property
    def all(self) -> list:
        return self.llm_tools.getall()


class LLMChainModel:
    system_prompt_template = """{existing_system_prompt}\n\nAdditional Contexts:{additional_context}\n\nYou have access to the following tools:\n\n{tools}\n\nAll content from tools are real-time data.\n\nUse a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation"""

    _overide_file_path = ""

    def __init__(self,
                 llm: BaseChatModel,
                 tools: list[BaseTool],
                 overide_chat_content: list = []) -> None:
        self.llm = llm
        self.tools = tools
        self.overide_chat_content = overide_chat_content

    def get_response_from_llm(self,
                              last_user_message: Message,
                              messages_copy: Chat,
                              full_context: str,
                              system_message: str,
                              standard_response: list[str] = [],
                              ) -> t.Dict[str, t.Any]:
        prompt = ChatPromptTemplate([
            ("system", self.system_prompt_template),
            MessagesPlaceholder('chat_history'),
            ("user", [{
                "type": "text",
                "text": "Input: {question}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)"
            }] + [img.as_lcMessageDict for img in last_user_message.content.media])
        ])

        executor = AgentExecutor(
            agent=create_structured_chat_agent(
                self.llm, self.tools, prompt),
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        return executor.invoke({
            "existing_system_prompt": system_message,
            "chat_history": messages_copy.as_list_of_lcMessages,
            "question": last_user_message.content.text,
            "additional_context": full_context,
            "standard_response": "\n".join(standard_response),
        })

    def invoke(self,
               messages: Chat,
               context: str,
               ) -> Message:
        messages_copy: Chat = copy.deepcopy(messages)

        system_message_content = None
        if messages_copy.system_message and messages_copy.system_message.content:
            system_message_content = messages_copy.system_message.content.text
            messages_copy.remove_system_message()

        last_user_message = messages_copy.last_message
        if not last_user_message:
            return Message('ai', "Please provide a message")
        if last_user_message.role != 'human':
            return Message('ai', "Please provide a human message")
        messages_copy.remove_last_message()

        # handle overide standard answer
        standard_response = ["Standard Response",
                             "You should follow the standard response below"]

        if self.overide_chat_content:
            for m in self.overide_chat_content:
                print(f"Checking {m=} against {last_user_message.content.text}")
                if m.get("question") in last_user_message.content.text:
                    standard_response.append(m.get("response"))


        # only include the standard response if there are more than the headers
        if len(standard_response) > 2:
            standard_response.append("End of Standard Response")
            print(f"Using {standard_response=}")
        else:
            standard_response = []

        full_context = "Current local datetime: {}\n".format(
            datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        full_context += context

        result = self.get_response_from_llm(
            last_user_message,
            messages_copy,
            full_context,
            system_message_content if system_message_content is not None else "",
            standard_response,
        )

        return Message('ai', MessageContent(result['output']))


class ChatLLM:
    chatRecords = Chat(
        system_message_string=(
            "You are a very powerful AI. "
            "Context maybe given to assist the assistant in providing better responses. "
            "For now you and the user is in Hong Kong. "
            "When asked for direction, provide as much details as possible. "
            "Use the google search tool to make sure your response are factical and can be sourced. "
            "You don't know much about the outside word, but with tools you can look up information. "
            "To provide the most accurate resault use the google search too make sure everyting you say are correct. "
            "When responding to the user provide as much contenxt as you can since you may need to answer more queries based on your responds. "
            "In Final Answer, make sure to output markdown whenever posible."
        )
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())

    def __init__(self,
                 llm_model: LLMChainModel,
                 chatId: str = "",
                 chatRecordFolderPath: str = './chat_data',
                 store_chat_records: bool = True
                 ) -> None:
        self.llm_model = llm_model
        self._chatId = chatId or self._chatId
        self.chatRecordFolderPath = chatRecordFolderPath
        self.store_chat_records = store_chat_records
        if store_chat_records and not os.path.exists(self.chatRecordFolderPath):
            os.makedirs(self.chatRecordFolderPath)
        if store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatId(self) -> str:
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        self._chatId = value
        if self.store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatRecordFilePath(self) -> str:
        return self.chatRecordFolderPath + "/" + self._chatId + ".json"

    def new_message(self, message: str, media: list[MessageContentMedia] = [], context: str = "") -> Message:
        if not message:
            return Message('system', "Please provide a message.")
        user_message = Message('human', MessageContent(message, media))

        self.chatRecords.append(user_message)
        ai_message = self.llm_model.invoke(self.chatRecords, context)
        self.chatRecords.append(ai_message)

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return Message('ai', ai_message.content.text)


if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    llm_model = LLMChainModel(
        llm=ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=1,
            max_tokens=8192,
            timeout=None,
            top_p=0.95,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        ),
        tools=LLMChainTools(credentials).all,
    )
    chatLLM = ChatLLM(llm_model)
    chatLLM.chatId = "a5d44788-0954-4a26-bc47-7fb7e2466537"
    while True:
        msg = input("Human: ")
        if msg == "EXIT":
            break
        if not msg:
            continue

        media_content = []
        if ':image' in msg:
            while True:
                image_path = input("Image Path: ")
                if image_path == "DONE":
                    break
                try:
                    with open(image_path, 'rb') as file:
                        image_data = file.read()
                    encoded_image = base64.b64encode(
                        image_data).decode('ASCII')
                    format = image_path.split('.')[-1]
                    media = MessageContentMedia(
                        format=format, data=encoded_image)
                    media_content.append(media)
                except Exception as e:
                    pass

            msg = msg.replace(':image', '')

        response = chatLLM.new_message(msg, media_content)
        response.lcMessage.pretty_print()
        print(f"AI({chatLLM.chatId}): " + response.content.text)
