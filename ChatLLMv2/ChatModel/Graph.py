import typing as t
import typing_extensions as te

from langgraph.graph import StateGraph, START, END  # type: ignore
from langgraph.graph.message import add_messages  # type: ignore

from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..DataHandler import ChatRecord, ChatMessage
from . import BaseModel


class State(te.TypedDict):
    messages: t.Annotated[list[t.Union[AIMessage, SystemMessage, HumanMessage]], add_messages]


class GraphModel(BaseModel):
    """Graph model class for language model interactions."""

    def __init__(self,
                 llm: BaseChatModel | None = None,
                 tools: list[BaseTool] = [],
                 overideChatContent: list[str] = [],
                 overideDirectOutput: bool = False,
                 ) -> None:
        super().__init__(llm, tools, overideChatContent, overideDirectOutput)
        """
        Initialize a GraphModel instance.

        :param llm: The language model to use.
        :param tools: A list of tools for the model to use.
        :param overideChatContent: A list of chat content to override.
        :param overideDirectOutput: Whether to directly output overide content.
        """
        if llm is None:
            raise Exception("Configuration Error, llm model cannot be None")

        def chatbot(state: State):
            return {"messages": [llm.invoke(state["messages"])]}  # type: ignore

        graphBuilder = StateGraph(State)
        graphBuilder.add_node("chatbot", chatbot)  # type: ignore
        graphBuilder.add_edge(START, "chatbot")
        graphBuilder.add_edge("chatbot", END)
        self.graph = graphBuilder.compile()  # type: ignore

    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        """
        Invoke the model with a chat record and get the response message.

        :param chatRecord: The chat record to process.
        :return: The response message from the model.
        """
        response = self.graph.invoke({
            "messages": chatRecord.asLcMessages
        })
        return ChatMessage("ai", str(response["messages"][-1].content))  # type: ignore
