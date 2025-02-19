import logging
import typing as t
import typing_extensions as te

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


from .Base import BaseModel
from .Property import AdditionalLLMProperty
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

    class State(te.TypedDict):
        messages: t.Annotated[list[t.Union[AIMessage, SystemMessage, HumanMessage]], add_messages]

    def chatbot(self):

        def executer(state: 'Model.State'):
            return {"messages": [self.llm.invoke(state["messages"])]}

        return executer

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm)
        self.graphBuilder = StateGraph(self.State)
        self.graphBuilder.add_node("chatbot", self.chatbot())
        self.graphBuilder.add_edge(START, "chatbot")
        self.graphBuilder.add_edge("chatbot", END)
        self.graph = self.graphBuilder.compile()


class GraphModel(BaseModel):
    """Graph model class for language model interactions."""

    def __init__(self,
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalLLMProperty | None = None,
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
        graph = Model(self.llm).graph
        response = graph.invoke({
            "messages": chatRecord.asLcMessages
        })
        return ChatMessage("ai", str(response["messages"][-1].content))  # type: ignore
