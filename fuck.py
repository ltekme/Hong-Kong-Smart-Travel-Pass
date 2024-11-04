import os
import typing as t
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import ToolNode
from google.oauth2.service_account import Credentials
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class MessagesState(t.TypedDict):
    messages: t.Annotated[list, add_messages]


# Load credentials
credentials_path = os.getenv("GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

# Initialize tools
tools = []

# Initialize LLM
llm = ChatVertexAI(
    model="gemini-1.5-pro-002",
    credentials=credentials,
    project=credentials.project_id,
    region="us-central1",
)


def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm.invoke({"messages": messages})
    return {"messages": [response]}


# Define workflow
workflow = StateGraph(MessagesState)
workflow.add_node("Request Hub Agent", call_model)
workflow.add_node("Transport Agent", call_model)
# workflow.add_node("Travel Agent", call_model)
workflow.add_node("Weather Agent", call_model)
# workflow.add_node("Attraction Agent", call_model)
workflow.add_node("Translate Agent", call_model)
workflow.add_node("Personalization", call_model)
workflow.add_node("Food Agent", call_model)

# workflow.add_node("Transportation tools", ToolNode(tools))
workflow.add_node("Weather Tools", ToolNode(tools))
workflow.add_node("Food tools", ToolNode(tools))
# workflow.add_node("External Info tools", ToolNode(tools))

workflow.add_edge(START, "Request Hub Agent")


def hub_cond_foodAg(state):
    pass


workflow.add_conditional_edges(
    "Request Hub Agent", hub_cond_foodAg, ["Food Agent"])


def hub_cond_WeatherAg(state):
    pass


workflow.add_conditional_edges(
    "Request Hub Agent", hub_cond_WeatherAg, ["Weather Agent"]
)


def foodAg_cond_foodTool(state):
    pass


workflow.add_conditional_edges(
    "Food Agent", foodAg_cond_foodTool, ["Food tools"]
)


def WeatherAg_cond_WeatherTool(state):
    pass


workflow.add_conditional_edges(
    "Weather Agent", WeatherAg_cond_WeatherTool, ["Weather Tools"],
)


def WeatherAg_cond_RequestHUubAg(state):
    pass


workflow.add_conditional_edges(
    "Weather Agent", WeatherAg_cond_RequestHUubAg, ["Request Hub Agent"])


def TransportAg_cond_WeatherAg(state):
    pass


def WeatherAg_cond_edges(state):
    pass


workflow.add_conditional_edges(
    "Transport Agent", TransportAg_cond_WeatherAg, "Weather Agent"
)


workflow.add_conditional_edges(
    "Weather Agent", WeatherAg_cond_edges, "Transport Agent"
)


workflow.add_edge("Weather Tools", "Weather Agent")
workflow.add_edge("Food tools", "Food Agent")
workflow.add_edge("Food Agent", "Personalization")
workflow.add_edge("Personalization", "Request Hub Agent")
workflow.add_edge("Request Hub Agent", "Translate Agent")
workflow.add_edge("Translate Agent", END)

# Compile and save the workflow graph
app = workflow.compile()
with open("./data/graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())

# # Run the application
# prompt = input(": ")
# stream = app.stream(
#     {"messages": [("human", prompt)]},
#     stream_mode="values",
#     debug=True,
# )
# print(app.get_prompts(stream))
# for chunk in stream:
#     chunk["messages"][-1].pretty_print()
