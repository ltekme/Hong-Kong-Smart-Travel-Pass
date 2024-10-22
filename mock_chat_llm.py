import os
import json
import uuid
import copy
import base64
import requests
import typing as t

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import Tool, create_structured_chat_agent, AgentExecutor

from google.oauth2.service_account import Credentials


class MessageContentImage:
    def __init__(self, format: str, data: str) -> None:
        """ Message content image class
        format: string representation of image format => ['jpg', 'png', ...]
        data: string representation of image data in base64 fomat => ['8nascCaAX==']
        """
        self.format = format
        self.data = data

    @property
    def uri(self) -> str:
        """Return the image uri in the format of JS data as URL"""
        return f"data:image/{self.format};base64,{self.data}"

    @staticmethod
    def from_uri(uri: str) -> None:
        format = uri.split(';')[0].split('/')[1]
        data = uri.split(',')[1]
        return MessageContentImage(format=format, data=data)

    @property
    def as_lcMessageDict(self) -> dict:
        return {
            "type": "image_url",
            "image_url": {"url": self.uri}
        }


class MessageContent:
    def __init__(self, text: str, images: list[MessageContentImage] = []) -> None:
        self.text = text
        self.images = images


class Message:
    def __init__(self, role: t.Literal["ai", "human", "system"], content: MessageContent | str) -> None:
        self.role: t.Literal["ai", "human", "system"] = role
        if type(content) == str:
            self.content: MessageContent = MessageContent(content)
        if type(content) == MessageContent:
            self.content: MessageContent = content

    @property
    def message_list(self) -> list[dict[str, str]]:
        """Return the human message list in the format of langchain template message"""
        return [{
            "type": "text",
            "text": self.content.text
        }] + [image.as_lcMessageDict for image in self.content.images]

    @property
    @staticmethod
    def lcMessageMapping(self) -> dict[str, t.Union[AIMessage, SystemMessage, HumanMessage]]:
        """Mapping of role text to Langchain message object"""
        return {
            "ai": AIMessage,
            "system": SystemMessage,
            "human": HumanMessage
        }

    @property
    def lcMessage(self):
        """Return langchain message object based on the role
        => AIMessage, SystemMessage, HumanMessage
        => AIMessage(content="Hello, How can I help you?")
        """
        return self.lcMessageMapping[self.role](content=self.message_list)


class Chat:

    _chat_messages: list[Message] = []

    def __init__(self, system_message_string: str | None = None) -> None:
        """Chat class to store chat messages
        system_message_string: string representation of system message
        """
        if system_message_string:
            # Append System Messaeg
            system_message_content = MessageContent(system_message_string)
            system_message = Message('system', system_message_content)
            self._chat_messages.append(system_message)

    @property
    def as_list_of_lcMessages(self) -> list[HumanMessage | AIMessage | SystemMessage]:
        return [msg.lcMessage for msg in self._chat_messages]

    def append(self, chatMessage: Message) -> None:
        self._chat_messages.append(chatMessage)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            json.dump([{
                "role": msg.role,
                "content": msg.message_list
            }for msg in self._chat_messages], f, indent=4)

    def get_from_file(self, file_path: str) -> list:
        system_message_copy = self.system_message
        try:
            with open(file_path, 'r') as f:
                data_in_file = json.load(f)

            messages = []
            for msg in data_in_file:
                message_content_text = None
                message_content_images = []

                for content in msg['content']:
                    if content['type'] == 'text':
                        message_content_text = content['text']
                    if content['type'] == 'image_url':
                        message_content_images.append(
                            MessageContentImage.from_uri(
                                uri=content['image_url']['url'])
                        )

                messages.append(Message(
                    role=msg['role'],
                    content=MessageContent(
                        text=message_content_text if message_content_text else '',
                        images=message_content_images
                    ))
                )

            self._chat_messages = messages
            return self._chat_messages

        except FileNotFoundError:
            self._chat_messages = [system_message_copy]
            return self._chat_messages

        except json.JSONDecodeError:
            self._chat_messages = [system_message_copy]
            return self._chat_messages

    @ property
    def system_message(self) -> Message | None:
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            return self._chat_messages[0]
        return None

    @system_message.setter
    def system_message(self, value: str) -> None:
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            self._chat_messages[0].content = value
        else:
            self._chat_messages.insert(0, Message('system', value))

    def remove_system_message(self):
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            self._chat_messages.pop(0)
        return None

    @property
    def last_message(self) -> Message:
        return self._chat_messages[-1] if len(self._chat_messages) > 0 and self._chat_messages[-1].role != 'system' else None

    def remove_last_message(self):
        if len(self._chat_messages) > 0 and self._chat_messages[-1].role != 'system':
            self._chat_messages.pop(-1)
        return None


class LLMChainToos:

    @staticmethod
    def fetch_data(url: str, methoad: t.Literal['POST', 'GET'] = 'GET') -> requests.Response:
        return requests.request(method=methoad, url=url)

    @staticmethod
    def get_weather(location: str = None) -> str:
        lang = "en"
        tempectureUrlMapping = {
            "en": "https://rss.weather.gov.hk/rss/CurrentWeather.xml",
            "tc": "https://rss.weather.gov.hk/rss/CurrentWeather_uc.xml"
        }
        nineDatForcastUrl = f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang={
            lang}"
        tempecture = LLMChainToos.fetch_data(tempectureUrlMapping[lang])
        nineDatForcast = LLMChainToos.fetch_data(nineDatForcastUrl)
        return f"""The Following is XML information on the current tempecture and weather Status

{tempecture.content.decode()}

The Following is the JSON api response to get the forcasted weather for the next 9 days

{nineDatForcast.content.decode()}"""

    all: list[Tool] = [
        Tool(
            name="get_current_weather",
            func=get_weather,
            description="Used to get the current weather from loacation. Default Hong Kong. Input should be a single string for the location",
        )
    ]


class LLMChainModel:

    agent_system_message_template_string = """Respond to the human as helpfully and accurately as possible. You have access to the following tools:\n\n{tools}\n\nUse a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation\n\n"""

    tools = LLMChainToos.all

    def __init__(self,
                 credentials: Credentials,
                 model: str,
                 temperature: float,
                 max_tokens: int,
                 ):
        self.llm = ChatVertexAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=None,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        )

    def invoke(self, messages: Chat) -> Message:
        messages_copy: Chat = copy.deepcopy(messages)

        system_message_content = None
        last_user_message = messages_copy.last_message
        messages_copy.remove_last_message()

        if messages_copy.system_message:
            system_message_content = messages_copy.system_message.content
            messages_copy.remove_system_message()

        messages = [
            ("system", self.agent_system_message_template_string +
             system_message_content.text)
        ] + messages_copy.as_list_of_lcMessages
        messages.append(
            ("user", [
                {
                    "type": "text",
                    "text": last_user_message.content.text + "\n\n{agent_scratchpad}\n\n(reminder to respond in a JSON blob no matter what)"
                },
            ] + [img.as_lcMessageDict for img in last_user_message.content.images]
            )
        )

        # Debugging
        # print(messages)

        resault = AgentExecutor.from_agent_and_tools(
            agent=create_structured_chat_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=ChatPromptTemplate(messages=messages),
            ),
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,  # Handle any parsing errors gracefully
        ).invoke({})
        return Message('ai', resault['output'])


class ChatLLM:

    chatRecords = Chat(
        system_message_string=(
            "You are a very powerful AI. "
            "Context maybe given to assist the assistant in providing better responses. "
            "Answer the questions to the best of your ability. "
            "If you don't know the answer, just say you don't know. "
            "For now you and the user is in Hong Kong"
        )
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())

    def __init__(self,
                 credentials: Credentials,
                 model: str = "gemini-1.5-pro",
                 temperature: float = 0.9,
                 max_tokens: int = 4096,
                 chatRecordFolderPath: str = './chat_data',
                 chatId: str = None,
                 store_chat_records: bool = True):
        self.llm = LLMChainModel(
            credentials=credentials,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
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

    def new_message(self, message: str, images: list[MessageContentImage] = []) -> Message:
        if not message:
            return Message('', "Please provide a message.")
        if images != []:
            self.chatRecords.append(
                Message('human', MessageContent(message, images)))
        else:
            self.chatRecords.append(Message('human', message))

        resault = self.llm.invoke(self.chatRecords)

        self.chatRecords.append(Message('ai', resault.content))

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return Message('ai', resault.content)


if __name__ == "__main__":
    credentialsFiles = list(filter(lambda f: f.startswith(
        'gcp_cred') and f.endswith('.json'), os.listdir('.')))
    credentials = Credentials.from_service_account_file(
        credentialsFiles[0])
    chatLLM = ChatLLM(credentials)
    # chatLLM.chatId = "c0b8b2ce-8ba7-49b1-882f-a87eb4c10c1d"
    while True:
        msg = input("Human: ")
        if msg == "EXIT":
            break

        response = None
        images_content = []
        if ':image' in msg:
            while True:
                image_path = input("Image Path: ")
                if image_path == "DONE":
                    break
                with open(image_path, 'rb') as f:
                    images_content.append(
                        MessageContentImage(
                            format=image_path.split('.')[-1],
                            data=base64.b64encode(f.read()).decode('ASCII')))
            msg.replace(':image', '')

        response = chatLLM.new_message(msg, images_content)
        print(f"AI({chatLLM.chatId}): " + response.content.text)
