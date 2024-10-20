import os
import json
import uuid
import typing as t

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import Tool, create_structured_chat_agent, AgentExecutor

from google.oauth2.service_account import Credentials


class ChatMessage:

    def __init__(self, role: str, content: str, **kwargs) -> None:
        self.role = role
        self.message = content

    def prompt_message(self):
        roles = {
            "user": HumanMessage,
            "ai": AIMessage,
            "system": SystemMessage,
        }
        message = roles.get(self.role, None)
        if not message:
            raise ValueError(f"role must be one of {roles.keys()}")
        return message(content=self.message)

    @property
    def as_dict(self):
        return {
            "role": self.role,
            "content": self.message,
        }

    @property
    def content(self) -> str:
        return self.message


class ChatMessages:

    _chat_messages: t.List[ChatMessage] = []

    def __init__(self, system_message_string: str | None = None) -> None:
        if system_message_string:
            self._chat_messages.append(
                ChatMessage('system', system_message_string))

    @property
    def as_list(self) -> list[ChatMessage]:
        return self._chat_messages

    @property
    def as_list_of_lcMessages(self) -> list[HumanMessage | AIMessage | SystemMessage]:
        return [chatMessage.prompt_message() for chatMessage in self._chat_messages]

    def append(self, chatMessage: ChatMessage) -> None:
        if chatMessage.role not in ['user', 'ai']:
            raise ValueError("role must be one of ['user', 'ai']")
        self._chat_messages.append(chatMessage)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            json.dump([chatMessage.as_dict
                      for chatMessage in self._chat_messages], f, indent=4)

    def get_from_file(self, file_path: str) -> list:
        system_message = None
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            system_message = self._chat_messages[0]
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self._chat_messages = []
            if system_message:
                self._chat_messages.append(system_message)
            return self._chat_messages
        try:
            with open(file_path, 'r') as f:
                data_in_file = json.load(f)
            self._chat_messages = [ChatMessage(**msg) for msg in data_in_file]
            if len(self._chat_messages) > 0 and system_message:
                if self._chat_messages[0].role != 'system':
                    self._chat_messages.insert(0, system_message)
                if self._chat_messages[0].role == 'system' and self._chat_messages[0].message != system_message.message:
                    self._chat_messages[0].message = system_message.message
            return self._chat_messages
        except json.JSONDecodeError:
            self._chat_messages = []
            if system_message:
                self._chat_messages.append(system_message)
            return self._chat_messages


class LLMChainToos:

    @staticmethod
    def get_weather(location: str) -> str:
        return "sunny"

    weather_tool = Tool(
        name="get_current_weather",
        func=get_weather,
        description="Used to get the current weather from loacation.",
    )


class LLMChainModel:

    # prompt = hub.pull("hwchase17/structured-chat-agent")
    # Clone from hum as I can't be bothered to create another API key
    prompt = ChatPromptTemplate(messages=[
        ("system", """Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{{
  "action": "Final Answer",
  "action_input": "Final response to human"
}}

Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation"""),
        MessagesPlaceholder("chat_history"),
        ("user", """{input}

{agent_scratchpad}

 (reminder to respond in a JSON blob no matter what)"""),
    ])

    tools = [LLMChainToos.weather_tool]

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

    def invoke(self, messages: ChatMessages) -> ChatMessage:
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,  # Handle any parsing errors gracefully
        )
        resault = agent_executor.invoke({
            "input": messages.as_list_of_lcMessages[-1].content,
            "chat_history": messages.as_list_of_lcMessages[0:-1]
        })
        return ChatMessage('ai', resault['output'])


class ChatLLM:

    chatRecords = ChatMessages(
        system_message_string=(
            "You are a very powerful AI. "
            "Context maybe given to assist the assistant in providing better responses. "
            "Answer the questions to the best of your ability. "
            "If you don't know the answer, just say you don't know. "
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

    def new_message(self, message: str) -> ChatMessage:
        if not message:
            return ChatMessage('', "Please provide a message.")
        self.chatRecords.append(ChatMessage('user', message))

        resault = self.llm.invoke(self.chatRecords)

        self.chatRecords.append(ChatMessage('ai', resault.content))

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return ChatMessage('ai', resault.content)


if __name__ == "__main__":
    credentialsFiles = list(filter(lambda f: f.startswith(
        'gcp_cred') and f.endswith('.json'), os.listdir('.')))
    credentials = Credentials.from_service_account_file(
        credentialsFiles[0])
    chatLLM = ChatLLM(credentials)
    # chatLLM.chatId = "0779b6cf-0d3a-4ab1-aaeb-86ff51e09f04"
    while True:
        msg = input("Human: ")
        if msg == "exit":
            break
        print(f"AI({chatLLM.chatId}): " + chatLLM.new_message(msg).message)
