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

from .Base import BaseModel
from .Property import AdditionalModelProperty
from ..DataHandler import ChatRecord, ChatMessage

logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class Model(BaseModel):

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
                 ) -> None:
        super().__init__(llm, additionalLLMProperty)
        promptTemplate = ChatPromptTemplate([
            ("system", self.prompt),
            MessagesPlaceholder("messages")
        ])
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
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalModelProperty,
                 ) -> None:
        super().__init__(llm, additionalLLMProperty)
        self.llm = llm
        self.additionalLLMProperty = additionalLLMProperty

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        graph = Model(self.llm, additionalLLMProperty=self.additionalLLMProperty)
        response = graph.invoke(chatRecord)
        return response
