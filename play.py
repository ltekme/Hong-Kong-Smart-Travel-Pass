import os
import typing as t
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import ToolNode
from google.oauth2.service_account import Credentials
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import chat_llm as cllm


class MessagesState(t.TypedDict):
    messages: t.Annotated[list, add_messages]


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


# Load credentials
credentials_path = os.getenv("GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

# Initialize tools
tools = cllm.LLMChainTools.all

# Initialize LLM
llm = ChatVertexAI(
    model="gemini-1.5-pro-002",
    credentials=credentials,
    project=credentials.project_id,
    region="us-central1",
)


def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm.invoke({messages: messages})
    return {"messages": [response]}


# Define workflow
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# Compile and save the workflow graph
app = workflow.compile()
with open("./data/graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())

# Run the application
prompt = input(": ")
stream = app.stream(
    {"messages": [("human", prompt)]},
    stream_mode="values",
    debug=True,
)
print(app.get_prompts(stream))
for chunk in stream:
    chunk["messages"][-1].pretty_print()
