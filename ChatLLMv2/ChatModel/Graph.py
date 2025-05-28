import logging

import typing as t
import typing_extensions as te

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts.chat import MessagesPlaceholder

from google.oauth2.service_account import Credentials
from langchain_google_vertexai import ChatVertexAI, HarmBlockThreshold, HarmCategory

from .Base import BaseModel
from .Property import AdditionalModelProperty, InvokeContextValues
from ..DataHandler import ChatRecord, ChatMessage

logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class Model:

    prompt = (
        "You are a travel assistant designed to support a tourist in their journy."
        # "You have access to real-time date, including time, weather, and more."
        # "Your primary task is to help the tourist plan their trip and "
        # "provide assistance on their question. "
        # "Use markdown if possible. "
        # "The tool you have will provide realtime data. "
        "Use tools avalable to provide the most accurate infromation "
    )

    class State(te.TypedDict):
        messages: t.Annotated[list[t.Union[AIMessage, SystemMessage, HumanMessage]], add_messages]

    def chatbot(self):
        def executer(state: 'Model.State'):
            return {"messages": [self.llmWithTool.invoke(state["messages"])]}  # type: ignore
        return executer

    def checkToolUse(self):
        def executor(state: 'Model.State'):
            return "tool" if state['messages'][-1].tool_calls else END  # type: ignore
        return executor

    def __init__(self,
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalModelProperty,
                 contextValues: InvokeContextValues,
                 ) -> None:
        """
        Initialize a Model instance.

        :param llm: The language model to use for generating responses.
        :param additionalLLMProperty: Additional properties for the model.
        :param contextValues: Additional context values for the invocation.
        :return: None
        """
        promptTemplate = ChatPromptTemplate([
            ("system", self.prompt),
            ("system", (
                f"<context>"
                f"  <location>{contextValues.location}</location>"
                f"  <utctime>{contextValues.utctime}</utctime>"
                f"</context>"
            )),
            MessagesPlaceholder("messages")
        ])
        self.llm = llm
        self.llmWithTool = promptTemplate | self.llm.bind_tools(additionalLLMProperty.llmTools)  # type: ignore

        self.graphBuilder = StateGraph(self.State)
        self.graphBuilder.add_node("chatbot", self.chatbot())  # type: ignore
        self.graphBuilder.add_node("tool", ToolNode(tools=additionalLLMProperty.llmTools))  # type: ignore
        self.graphBuilder.add_edge("tool", "chatbot")
        self.graphBuilder.add_conditional_edges("chatbot", self.checkToolUse(), ["tool", END])
        self.graphBuilder.add_edge(START, "chatbot")
        self.graph = self.graphBuilder.compile()  # type: ignore

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        response = ""
        for chunk in self.graph.stream({
            "messages": chatRecord.asLcMessages
        }, stream_mode="updates"):
            try:
                response += chunk['chatbot']['messages'][-1].content
            except:
                continue
            logger.debug(f"[GRAPH DEBUG] => {chunk}")
        return ChatMessage("ai", str(response))


class GraphModel(BaseModel):
    """Graph model class for language model interactions."""

    def __init__(self,
                 additionalLLMProperty: AdditionalModelProperty,
                 gcpCredentials: t.Optional[Credentials] = None,
                 ) -> None:
        super().__init__(additionalLLMProperty)
        if gcpCredentials is None:
            logger.warning("No GCP credentials provided, Improper setup will cause issues.")
        self.llm = ChatVertexAI(
            model="gemini-2.0-flash-001",
            temperature=1,
            max_retries=2,
            credentials=gcpCredentials,
            project=gcpCredentials.project_id if gcpCredentials else None,  # type: ignore
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.OFF,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.OFF,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.OFF,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.OFF,
            },
            response_mime_type="application/json",
            # response_schema={"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "action_input": {"type": "STRING"}}, "required": ["action", "action_input"]},
        )

    def invoke(self, chatRecord: ChatRecord, contextValues: InvokeContextValues) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :param contextValues: Additional context values for the invocation.
        :return: The response message from the model.
        """
        model = Model(self.llm, self.additionalLLMProperty, contextValues)
        return model.invoke(chatRecord)
