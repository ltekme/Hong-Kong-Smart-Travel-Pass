import os
import typing as t
import typing_extensions as tx

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import ToolNode

from google.oauth2.service_account import Credentials

import chat_llm as cllm


class LLMGraphModel:

    tools = cllm.LLMChainTools.all

    def _lcNode_chatbot_invoke(self, state: list):
        return {"messages": [self.llm.invoke(state["messages"])]}

    def __init__(self,
                 credentials: Credentials,
                 **kwargs
                 ) -> None:
        self.credentials = credentials
        self.llm = ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=1,
            max_tokens=8192,
            timeout=None,
            top_p=0.95,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        ).bind_tools(self.tools)

        graph_builder = StateGraph(list)
        graph_builder.add_node("bot_invoke", self._lcNode_chatbot_invoke)
        graph_builder.add_node("all_tools", ToolNode(self.tools))
        graph_builder.add_edge("bot_invoke", "all_tools")
        graph_builder.add_edge(START, "bot_invoke")
        graph_builder.add_edge("bot_invoke", END)
        self.graph = graph_builder.compile()

    def show(self, img_path: str) -> None:
        with open(img_path, "wb") as f:
            f.write(self.graph.get_graph().draw_mermaid_png())

    def invoke(self, message: cllm.Message) -> AIMessage:
        if type(message) != cllm.Message:
            message = cllm.Message('human', message)

        for event in self.graph.stream({"messages": [("user", message.content.text)]}):
            for value in event.values():
                return value["messages"][0]


if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    llmgraph = LLMGraphModel(credentials=credentials)
    llmgraph.show("./data/graph.png")

    while True:
        try:
            user_input = input(': ')
            # clear input line
            print('\033[1A\033[K', end="")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            HumanMessage(user_input).pretty_print()
            resault = llmgraph.invoke(user_input)
            resault.pretty_print()
        except KeyboardInterrupt:
            print("bye !")
            break
