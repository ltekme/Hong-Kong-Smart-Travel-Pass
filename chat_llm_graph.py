import os
import typing as t
import typing_extensions as tx

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import ToolNode

from langchain_core.language_models.chat_models import BaseChatModel

from google.oauth2.service_account import Credentials

import chat_llm as cllm


class LgController:

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self.node = "controller"
        self.action = self._invoke

    def _invoke(self, state: dict):
        print(f"Invoke Controller Node {state['messages'][-1]=}")
        return {"messages": [self.llm.invoke(state["messages"])]}

    @property
    def nodeKwargs(self):
        return {
            "node": self.node,
            "action": self.action,
        }


class LLMGraphModel(cllm.LLMModelBase):
    def __init__(self,
                 llm: BaseChatModel,
                 ) -> None:

        controller = LgController(llm)

        graph_builder = StateGraph(dict)
        graph_builder.add_node(**controller.nodeKwargs)
        graph_builder.add_edge(START, controller.node)
        graph_builder.add_edge(controller.node, END)
        self.graph = graph_builder.compile()

    def show(self, img_path: str) -> None:
        with open(img_path, "wb") as f:
            f.write(self.graph.get_graph().draw_mermaid_png())

    def invoke(self, messages: cllm.Chat, context=None) -> cllm.Message:
        if not isinstance(messages, cllm.Chat):
            raise ValueError("messages must be an instance of Chat")

        messages.remove_system_message()
        # print(messages.as_list_of_lcMessages)
        for event in self.graph.stream({"messages": messages.as_list_of_lcMessages}):
            for value in event.values():
                return cllm.Message("ai", str(value["messages"][0].content))
        return cllm.Message("ai", "No response generated.")
