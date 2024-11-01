import os
import json
import uuid
import copy
import base64
import typing as t
import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import create_structured_chat_agent, AgentExecutor

from google.oauth2.service_account import Credentials

# from mtr import MTRApi
from llm_tools import LLMTools

from dotenv import load_dotenv
load_dotenv()


# GCP_DATA_SA_CREDENTIAL_PATH
# GCP_AI_SA_CREDENTIAL_PATH
# need to be set in the .env file


class MessageContentMedia:
    def __init__(self, format: str, data: str, media_type="image") -> None:
        """ Message content image class
        format: string representation of image format => ['jpg', 'png', ...]
        data: string representation of image data in base64 fomat => ['8nascCaAX==']
        """
        self.format = format
        self.data = data
        self.media_type = media_type

    @property
    def uri(self) -> str:
        """Return the image uri in the format of JS data as URL"""
        return f"data:{self.media_type}/{self.format};base64,{self.data}"

    @property
    def as_lcMessageDict(self) -> dict:
        return {
            "type": "image_url",
            "image_url": {"url": self.uri}
        }

    @staticmethod
    def from_uri(uri: str) -> t.Union["MessageContentMedia", None]:
        try:
            if not uri.startswith('data:'):
                # TODO: fetch data from url or something else
                pass
            header = uri.split(';')[0].split('/')
            format = header[1]
            media_type = header[0].split(':')[1]
            data = uri.split(',')[1]
            return MessageContentMedia(format=format, data=data, media_type=media_type)
        except:
            return None


class MessageContent:
    def __init__(self, text: str, media: list[MessageContentMedia] = []) -> None:
        self.text = text
        self.media = media


class Message:
    def __init__(self, role: t.Literal["ai", "human", "system"], content: MessageContent | str) -> None:
        self.role: t.Literal["ai", "human", "system"] = role
        if type(content) == MessageContent:
            self.content: MessageContent = content
            return
        self.content: MessageContent = MessageContent(str(content))

    @property
    def message_list(self) -> list[dict[str, str]]:
        """Return the human message list in the format of langchain template message"""
        return [{
            "type": "text",
            "text": str(self.content.text)
        }] + [image.as_lcMessageDict for image in self.content.media]

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
    def lcMessage(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
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
    def as_list(self) -> list[Message]:
        return self._chat_messages

    @property
    def as_list_of_lcMessages(self) -> list[HumanMessage | AIMessage | SystemMessage]:
        return [msg.lcMessage for msg in self._chat_messages]

    def append(self, chatMessage: Message) -> None:
        self._chat_messages.append(chatMessage)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            messages = [
                {"role": msg.role, "content": msg.message_list}
                for msg in self._chat_messages]
            json.dump(messages, f, indent=4)

    def get_from_file(self, file_path: str) -> list:
        system_message_copy = self.system_message
        try:
            with open(file_path, 'r') as f:
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

        except json.JSONDecodeError:
            if system_message_copy is not None:
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


class LLMChainTools:
    # Preinitialise Tools
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    llm_tools = LLMTools(credentials=credentials, verbose=True)
    all = llm_tools.all


class LLMChainModel:

    # prompt = hub.pull("hwchase17/structured-chat-agent")
    # Clone from hum as I can't be bothered to create another API key
    system_prompt_template = """{existing_system_prompt}\n\nAdditional Contexts:{additional_context}\n\nYou have access to the following tools:\n\n{tools}\n\nAll content from tools are real-time data.\n\nUse a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation"""

    tools = LLMChainTools.all

    def __init__(self,
                 credentials: Credentials,
                 model: str,
                 temperature: float,
                 top_p: float,
                 max_tokens: int,
                 ):
        self.llm = ChatVertexAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=None,
            top_p=top_p,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        )

    def invoke(self, messages: Chat, context: str) -> Message:
        messages_copy: Chat = copy.deepcopy(messages)

        system_message_content = None
        if messages_copy.system_message:
            system_message_content = messages_copy.system_message.content
            messages_copy.remove_system_message()

        last_user_message = messages_copy.last_message
        messages_copy.remove_last_message()

        # additional context for llm
        full_context = "Current local datetime: {}\n".format(
            datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        full_context += context

        prompt = ChatPromptTemplate([
            ("system", self.system_prompt_template),
            MessagesPlaceholder('chat_history'),
            ("user", [{
                "type": "text",
                "text": "Input: {question}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)"
            }] + [img.as_lcMessageDict for img in last_user_message.content.media])
        ])

        # for img in last_user_message.content.media:
        #     print(img.as_lcMessageDict)

        agent = create_structured_chat_agent(
            self.llm, self.tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # See thoughts
            handle_parsing_errors=True,  # Handle any parsing errors gracefully
        )
        resault = executor.invoke({
            "existing_system_prompt": system_message_content.text if system_message_content is not None else "",
            "chat_history": messages_copy.as_list_of_lcMessages,
            "question": last_user_message.content.text,
            "additional_context": full_context
        })

        # Debugging
        # print(agent.get_prompts()[0])
        # return Message('ai', "debugging output")
        return Message('ai', MessageContent(resault['output']))


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
            "output markdown whenever posible, in the Final Answer response"
        )
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())

    def __init__(self,
                 credentials: Credentials,
                 LLM_Class=LLMChainModel,
                 model: str = "gemini-1.5-pro-002",
                 temperature: float = 1,
                 top_p: float = 0.95,
                 max_tokens: int = 8192,
                 chatRecordFolderPath: str = './chat_data',
                 chatId: str = None,
                 store_chat_records: bool = True
                 ) -> None:
        self.llm = LLM_Class(
            credentials=credentials,
            model=model,
            top_p=top_p,
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

    def new_message(self, message: str, media: list[MessageContentMedia] = [], context: str = "") -> Message:
        if not message:
            return Message('', "Please provide a message.")
        if media != []:
            self.chatRecords.append(
                Message('human', MessageContent(message, media)))
        else:
            self.chatRecords.append(Message('human', message))

        resault = self.llm.invoke(self.chatRecords, context)

        self.chatRecords.append(resault)

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return Message('ai', resault.content.text)


if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    chatLLM = ChatLLM(credentials)
    chatLLM.chatId = "a5d44788-0954-4a26-bc47-7fb7e2466537"
    while True:
        msg = input("Human: ")
        if msg == "EXIT":
            break
        if not msg:
            pass

        # process image
        response = None
        media_content = []
        if ':image' in msg:
            while True:
                image_path = input("Image Path: ")
                if image_path == "DONE":
                    break
                with open(image_path, 'rb') as f:
                    media_content.append(
                        MessageContentMedia(
                            format=image_path.split('.')[-1],
                            data=base64.b64encode(f.read()).decode('ASCII')))
            msg.replace(':image', '')

        response = chatLLM.new_message(msg, media_content)
        # print("ChatID: " + chatLLM.chatId)
        # print(response.lcMessage.pretty_print())
        print(f"AI({chatLLM.chatId}): " + response.content.text)
