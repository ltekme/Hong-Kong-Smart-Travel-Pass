import os
import json
import uuid
import copy
import base64
import requests
import typing as t

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import StructuredTool, Tool
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_google_community import GoogleSearchAPIWrapper

from pydantic import BaseModel
from google.oauth2.service_account import Credentials

from openrice import OpenriceApi
from mtr import MTRApi
from LLM_Tool_API import all as all_llm_tools

from dotenv import load_dotenv
load_dotenv()


# GCP_DATA_SA_CREDENTIAL_PATH
# GCP_AI_SA_CREDENTIAL_PATH
# need to be set in the .env file


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
        if not self.content.text:
            self.content = MessageContent("No input")

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
                message_content_images = []

                for content in msg['content']:
                    if content['type'] == 'text':
                        message_content_text = content['text']
                    if content['type'] == 'image_url':
                        message_content_images.append(
                            MessageContentImage.from_uri(content['image_url']['url']))

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
    lang = "en"

    class EmptyArgs(BaseModel):
        pass

    @staticmethod
    def fetch_data(url: str, methoad: t.Literal['POST', 'GET'] = 'GET') -> str:
        return requests.request(method=methoad, url=url).content.decode('utf-8')

    class OpenriceRecommendationArgs(BaseModel):
        district_id: t.Optional[int] = None
        landmark_id: t.Optional[int] = None
        keyword: t.Optional[str] = None
        number_of_results: t.Optional[int] = 5
        starting_resault_index: t.Optional[int] = 0
        lang: t.Optional[str] = "en"

    @staticmethod
    def get_openrice_restaurant_recommendation(**kwargs) -> str:
        openrice = OpenriceApi()
        return [openrice.prettify(restaurant) + '\n\n' for restaurant in openrice.
                search(
            district_id=kwargs.get('district_id'),
            landmark_id=kwargs.get('landmark_id'),
            keywords=kwargs.get('keyword'),
            count=kwargs.get('number_of_results', 5),
            start=kwargs.get('starting_resault_index', 0),
            lang=kwargs.get('lang', 'en')
        )]

    @staticmethod
    def get_openrice_districts_filter_list(**kwargs) -> list[dict[int, str]]:
        openrice = OpenriceApi()
        district_filters = openrice.districts
        return [{district['districtId']: district['nameLangDict']['en']} for district in district_filters]

    @staticmethod
    def get_openrice_landmark_filter_list(**kwargs) -> list[dict[int, str]]:
        openrice = OpenriceApi()
        landmark_filters = openrice.landmarks
        return [{landmark['landmarkId']: landmark['nameLangDict']['en']} for landmark in landmark_filters]

    class PerformGoogleSearchArgs(BaseModel):
        query: str

    @staticmethod
    def perform_google_search(*args, **kwargs) -> str:
        google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if not google_api_key or not google_cse_id:
            return 'Google API Key or Google CSE ID is not provided. Cannot Perform Google Search'
        search = GoogleSearchAPIWrapper(
            google_api_key=google_api_key,
            google_cse_id=google_cse_id
        )
        # Assuming the first positional argument is the query
        query = args[0] if args else kwargs.get('query')
        if not query:
            return 'No query provided for Google Search'
        return search.run(query)

    @staticmethod
    def get_mtr_stations_info(**kwargs) -> str:
        credentials_path = os.getenv(
            "GCP_DATA_SA_CREDENTIAL_PATH", './gcp_cred-data.json')
        credentials = Credentials.from_service_account_file(credentials_path)
        mtrApi = MTRApi(credentials=credentials)
        return mtrApi.prettify_station(mtrApi.stations)

    class GetMtrStationFromName(BaseModel):
        station_name: str

    @staticmethod
    def get_mtr_station_from_station_name(station_name: str, **kwargs) -> str:
        credentials_path = os.getenv(
            "GCP_DATA_SA_CREDENTIAL_PATH", './gcp_cred-data.json')
        credentials = Credentials.from_service_account_file(credentials_path)
        mtrApi = MTRApi(credentials=credentials)
        station = mtrApi.get_station_from_station_name(station_name)
        if not station:
            return f"Station with name {station_name} not found"
        return mtrApi.prettify_station(station)

    class SearchMtrPathArgs(BaseModel):
        originStationId: int
        destinationStationId: int

    @staticmethod
    def search_mtr_path_between_stations(originStationId: int, destinationStationId: int, **kwargs) -> str:
        credentials_path = os.getenv(
            "GCP_DATA_SA_CREDENTIAL_PATH", './gcp_cred-data.json')
        credentials = Credentials.from_service_account_file(credentials_path)
        mtrApi = MTRApi(credentials=credentials)
        return mtrApi.get_from_and_to_station_path(originStationId, destinationStationId)

    all: list[Tool] = [
        Tool.from_function(
            name="get_content_from_url",
            func=fetch_data,
            description="Used to get the content from a url. Input should be a single string for the url",
            return_direct=True,
        ),
        StructuredTool(
            name="get_openrice_restaurant_recommendation",
            func=get_openrice_restaurant_recommendation,
            description="Used to get the restaurant recommendation from openrice. Default Hong Kong with no District. The district_id filter can be obtained from get_openrice_districts_filter_list tool. When no district id were found using the get_openrice_districts_filter_list tool, use the get_openrice_landmark_filter_list tool and see if the place exists in that list. The landmark_id filter can be obtained from the get_openrice_landmark_filter_list tool. Places like MTR stations will be in the landmark filter list. Input to this tool is optional. When no input is provided, general recommendataions will be provided. Real-time data from Openrice like the restaurant information(phone, links, ...) can be obtained using this tool. keyword argument can be used to narrow down the search for the restarant keywords, the keyword is not a search engine, it is used to filter restauract info. Provide the openRiceShortUrl when asked for a specific restaurant.",
            args_schema=OpenriceRecommendationArgs
        ),
        StructuredTool(
            name="get_openrice_landmark_filter_list",
            func=get_openrice_landmark_filter_list,
            description="Used to get list of landmarks from openrice to be used in the as landmark filter on get_openrice_restaurant_recommendation. No Input Should be provided. This list is limited to Openrice search landmark. If a place not exist in this list, try google searching the location of a place. e,g, amoy plaza is in Kowloon Bay",
            args_schema=EmptyArgs
        ),

        StructuredTool(
            name="get_openrice_districts_filter_list",
            func=get_openrice_districts_filter_list,
            description="Used to get the list of districts from openrice to be used as district filter on get_openrice_restaurant_recommendation. No Input Should be provided. This list is limited to Openrice search districts. When no matching district werre found, try using the get_openrice_landmark_filter_list tool, sometimes the place exists in the landmark filter list. If it sill doesn't exists, use the google_search tool to see if you can get a wider location that exists in the list.",
            args_schema=EmptyArgs
        ),
        StructuredTool(
            name="google_search",
            func=perform_google_search,
            description="Search Google for recent results.",
            args_schema=PerformGoogleSearchArgs
        ),
        StructuredTool(
            name="get_mtr_stations_info",
            func=get_mtr_stations_info,
            description="Get the list of MTR stations information. Line Station Sequence is the order of the station in the line. Line Station Direction is the direction of the station in the line. No Input Should be provided.",
            args_schema=EmptyArgs
        ),
        StructuredTool(
            name="search_mtr_path_between_stations",
            func=search_mtr_path_between_stations,
            description="Search the path between two MTR stations. Input should be two integers for the originStationId and destinationStationId. The station id can be obtained from the get_mtr_stations_info tool or get_mtr_station_from_station_name tool, when it is not found in the get_mtr_station_from_station_name, try get all the stations using the get_mtr_stations_info tool and find the station id from there, incase typo in the station name.",
            args_schema=SearchMtrPathArgs
        ),
        StructuredTool(
            name="get_mtr_station_from_station_name",
            func=get_mtr_station_from_station_name,
            description="Get the MTR station information from the station name. Input should be a single string for the station name. The station name can be in English or Chinese. The station name should be the exact name of the station. The station name can be obtained from the get_mtr_stations_info tool.",
            args_schema=GetMtrStationFromName
        )
    ] + all_llm_tools


class LLMChainModel:

    # prompt = hub.pull("hwchase17/structured-chat-agent")
    # Clone from hum as I can't be bothered to create another API key
    system_prompt_template = """Respond to the human as helpfully and accurately as possible. You have access to the following tools:\n\n{tools}\n\nAll content from tools are real-time data.\n\nUse a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation\n\n{existing_system_prompt}"""

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
        if messages_copy.system_message:
            system_message_content = messages_copy.system_message.content
            messages_copy.remove_system_message()

        last_user_message = messages_copy.last_message
        messages_copy.remove_last_message()

        prompt = ChatPromptTemplate([
            ("system", self.system_prompt_template),
            MessagesPlaceholder('chat_history'),
            ("user", [{
                "type": "text",
                "text": "Input: {question}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)"
            }] + [img.as_lcMessageDict for img in last_user_message.content.images])
        ])

        # Debugging
        # print(messages)

        agent = create_structured_chat_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # See thoughts
            handle_parsing_errors=True,  # Handle any parsing errors gracefully
        )
        resault = executor.invoke({
            "existing_system_prompt": system_message_content.text,
            "chat_history": messages_copy.as_list_of_lcMessages,
            "question": last_user_message.content.text
        })
        # Debugging
        # print(messages)
        return Message('ai', resault['output'])


class ChatLLM:

    chatRecords = Chat(
        system_message_string=(
            "You are a very powerful AI. "
            "Context maybe given to assist the assistant in providing better responses. "
            "Answer the questions to the best of your ability. "
            "If you don't know the answer, just say you don't know. "
            "For now you and the user is in Hong Kong. "
        )
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())

    def __init__(self,
                 credentials: Credentials,
                 model: str = "gemini-1.5-pro",
                 temperature: float = 0.5,
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

        self.chatRecords.append(resault)

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return Message('ai', resault.content.text)


if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    chatLLM = ChatLLM(credentials)
    # chatLLM.chatId = "7b5bb9e7-ceff-42a1-abc4-af6198f96390"
    while True:
        msg = input("Human: ")
        if msg == "EXIT":
            break
        if not msg:
            pass

        # process image
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
        # print("ChatID: " + chatLLM.chatId)
        # print(response.lcMessage.pretty_print())
        print(f"AI({chatLLM.chatId}): " + response.content.text)
