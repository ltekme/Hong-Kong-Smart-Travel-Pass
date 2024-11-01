import os
import typing_extensions as tx
import typing as t
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
import langchain_core.messages as lc_messages
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import ToolNode
from pydantic import Discriminator, Field, Tag
from google.oauth2.service_account import Credentials


import chat_llm as cllm


class MessagesState(t.TypedDict):
    messages: t.Annotated[list, add_messages]


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)
tools = cllm.LLMChainTools.all


llm = ChatVertexAI(
    model="gemini-1.5-pro-002",
    temperature=1,
    max_tokens=8192,
    timeout=None,
    top_p=0.95,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id,
    region="us-central1",
)


def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app = workflow.compile()
with open("./data/graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())


prompt = input(": ")
for chunk in app.stream(
    {"messages": [("human", prompt)]},
    stream_mode="values",
    debug=True,
):
    chunk["messages"][-1].pretty_print()
